"""
HuntIQ — Generic Base Repository.

Provides reusable CRUD operations for all domain repositories.
Every domain repository inherits from BaseRepository and can
override or extend these methods.

Usage:
    class JobRepository(BaseRepository[Job]):
        model = Job

    repo = JobRepository(session)
    job = await repo.get_by_id("some-uuid")
    jobs = await repo.list(limit=20, offset=0)
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RecordNotFoundError
from app.core.logging import get_logger
from app.database.base import Base

logger = get_logger(__name__)

# Type variable for the ORM model class
ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic async repository providing common CRUD operations.

    Subclasses must set the `model` class attribute to the
    SQLAlchemy model class they manage.

    All methods accept and return ORM model instances.
    Business logic does NOT belong here — only data access.
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the repository with a database session.

        Args:
            session: An async SQLAlchemy session.
        """
        self.session = session

    # ==========================================================
    # Read Operations
    # ==========================================================

    async def get_by_id(self, record_id: str) -> ModelT | None:
        """
        Get a single record by its primary key.

        Args:
            record_id: The UUID primary key.

        Returns:
            The model instance, or None if not found.
        """
        return await self.session.get(self.model, record_id)

    async def get_by_id_or_raise(self, record_id: str) -> ModelT:
        """
        Get a single record by primary key, raising if not found.

        Args:
            record_id: The UUID primary key.

        Returns:
            The model instance.

        Raises:
            RecordNotFoundError: If no record with the given ID exists.
        """
        record = await self.get_by_id(record_id)
        if record is None:
            raise RecordNotFoundError(
                entity=self.model.__name__,
                identifier=record_id,
            )
        return record

    async def get_by_field(self, field: str, value: Any) -> ModelT | None:
        """
        Get a single record by an arbitrary field value.

        Args:
            field: The column name to filter on.
            value: The value to match.

        Returns:
            The first matching model instance, or None.
        """
        column = getattr(self.model, field)
        stmt = select(self.model).where(column == value)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        order_by: str | None = None,
        descending: bool = True,
        filters: dict[str, Any] | None = None,
    ) -> Sequence[ModelT]:
        """
        List records with pagination, ordering, and filtering.

        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip.
            order_by: Column name to order by (default: created_at).
            descending: Whether to sort in descending order.
            filters: Dict of {column_name: value} for equality filters.

        Returns:
            A sequence of model instances.
        """
        stmt = self._apply_filters(select(self.model), filters)
        stmt = self._apply_ordering(stmt, order_by, descending)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """
        Count records matching the given filters.

        Args:
            filters: Dict of {column_name: value} for equality filters.

        Returns:
            The count of matching records.
        """
        stmt = select(func.count()).select_from(self.model)
        if filters:
            for field_name, value in filters.items():
                column = getattr(self.model, field_name)
                stmt = stmt.where(column == value)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists(self, record_id: str) -> bool:
        """
        Check if a record with the given ID exists.

        Args:
            record_id: The UUID primary key.

        Returns:
            True if the record exists, False otherwise.
        """
        stmt = select(func.count()).select_from(self.model).where(
            self.model.id == record_id  # type: ignore[attr-defined]
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def list_by_ids(self, ids: list[str]) -> Sequence[ModelT]:
        """
        Get multiple records by their primary keys.

        Args:
            ids: List of UUID primary keys.

        Returns:
            A sequence of found model instances (may be shorter than input).
        """
        if not ids:
            return []
        stmt = select(self.model).where(
            self.model.id.in_(ids)  # type: ignore[attr-defined]
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # ==========================================================
    # Write Operations
    # ==========================================================

    async def create(self, **kwargs: Any) -> ModelT:
        """
        Create a new record.

        Args:
            **kwargs: Column values for the new record.

        Returns:
            The created model instance.
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def create_from_model(self, instance: ModelT) -> ModelT:
        """
        Persist an existing model instance.

        Args:
            instance: The model instance to persist.

        Returns:
            The persisted model instance (refreshed).
        """
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def bulk_create(self, records: list[dict[str, Any]]) -> list[ModelT]:
        """
        Create multiple records in a single batch.

        Args:
            records: List of dicts with column values.

        Returns:
            List of created model instances.
        """
        instances = [self.model(**data) for data in records]
        self.session.add_all(instances)
        await self.session.flush()
        for instance in instances:
            await self.session.refresh(instance)
        return instances

    async def update(self, record_id: str, **kwargs: Any) -> ModelT:
        """
        Update a record by its primary key.

        Args:
            record_id: The UUID primary key.
            **kwargs: Column values to update.

        Returns:
            The updated model instance.

        Raises:
            RecordNotFoundError: If no record with the given ID exists.
        """
        instance = await self.get_by_id_or_raise(record_id)
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def bulk_update(
        self,
        filters: dict[str, Any],
        values: dict[str, Any],
    ) -> int:
        """
        Update multiple records matching the given filters.

        Args:
            filters: Dict of {column_name: value} for equality filters.
            values: Dict of {column_name: new_value} to set.

        Returns:
            Number of records updated.
        """
        stmt = update(self.model)
        for field_name, value in filters.items():
            column = getattr(self.model, field_name)
            stmt = stmt.where(column == value)
        stmt = stmt.values(**values)
        result = await self.session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]

    # ==========================================================
    # Delete Operations
    # ==========================================================

    async def delete(self, record_id: str) -> bool:
        """
        Delete a record by its primary key.

        Args:
            record_id: The UUID primary key.

        Returns:
            True if a record was deleted, False if not found.
        """
        stmt = delete(self.model).where(
            self.model.id == record_id  # type: ignore[attr-defined]
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0  # type: ignore[union-attr]

    async def bulk_delete(self, ids: list[str]) -> int:
        """
        Delete multiple records by their primary keys.

        Args:
            ids: List of UUID primary keys to delete.

        Returns:
            Number of records deleted.
        """
        if not ids:
            return 0
        stmt = delete(self.model).where(
            self.model.id.in_(ids)  # type: ignore[attr-defined]
        )
        result = await self.session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]

    # ==========================================================
    # Query Helpers
    # ==========================================================

    def _apply_filters(
        self,
        stmt: Select[tuple[ModelT]],
        filters: dict[str, Any] | None,
    ) -> Select[tuple[ModelT]]:
        """Apply equality filters to a select statement."""
        if filters:
            for field_name, value in filters.items():
                column = getattr(self.model, field_name)
                if isinstance(value, list):
                    stmt = stmt.where(column.in_(value))
                elif value is None:
                    stmt = stmt.where(column.is_(None))
                else:
                    stmt = stmt.where(column == value)
        return stmt

    def _apply_ordering(
        self,
        stmt: Select[tuple[ModelT]],
        order_by: str | None,
        descending: bool,
    ) -> Select[tuple[ModelT]]:
        """Apply ordering to a select statement."""
        if order_by:
            column = getattr(self.model, order_by, None)
            if column is not None:
                stmt = stmt.order_by(column.desc() if descending else column.asc())
        elif hasattr(self.model, "created_at"):
            col = self.model.created_at  # type: ignore[attr-defined]
            stmt = stmt.order_by(col.desc() if descending else col.asc())
        return stmt
