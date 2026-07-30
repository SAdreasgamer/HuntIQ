"""
HuntIQ — SQLAlchemy Base Model and Mixins.

Defines the declarative base and reusable mixins that provide
common columns (id, timestamps, soft delete) to all ORM models.

Every model in the application inherits from Base, which
automatically provides:
- UUID primary key
- created_at / updated_at timestamps
- Consistent __repr__ and __tablename__ generation
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)


class Base(DeclarativeBase):
    """
    Declarative base for all HuntIQ ORM models.

    Provides automatic table naming and a consistent __repr__.
    All models should inherit from this class.
    """

    # Use the class name in snake_case as the default table name
    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        """Generate snake_case table name from class name."""
        name = cls.__name__
        # Convert CamelCase to snake_case
        result: list[str] = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append("_")
            result.append(char.lower())
        return "".join(result) + "s"

    def __repr__(self) -> str:
        """Generate a useful repr showing the model class and primary key."""
        pk_cols = [col.name for col in self.__table__.primary_key.columns]
        pk_vals = {col: getattr(self, col, None) for col in pk_cols}
        pk_str = ", ".join(f"{k}={v!r}" for k, v in pk_vals.items())
        return f"<{self.__class__.__name__}({pk_str})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            col.name: getattr(self, col.name)
            for col in self.__table__.columns
        }


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp columns.

    - created_at: Set automatically on insert (server-side)
    - updated_at: Set automatically on insert and update (server-side)
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Timestamp when the record was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the record was last updated",
    )


class UUIDPrimaryKeyMixin:
    """
    Mixin that adds a UUID primary key column.

    Uses Python-generated UUIDs for compatibility across
    SQLite and PostgreSQL.
    """

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="Unique identifier (UUID v4)",
    )


class SoftDeleteMixin:
    """
    Mixin that adds soft delete support.

    Instead of physically deleting records, they are marked
    with a deleted_at timestamp and filtered out of queries.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
        doc="Timestamp when the record was soft-deleted (null = active)",
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the record has been soft-deleted."""
        return self.deleted_at is not None


class NotesMixin:
    """Mixin that adds a notes text column."""

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="Free-form notes",
    )
