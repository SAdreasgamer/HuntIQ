"""
HuntIQ — Database Engine and Session Management.

Configures the async SQLAlchemy engine and session factory.
Provides dependency injection helpers for FastAPI routes.

Usage in FastAPI routes:
    from app.database.session import get_async_session

    @router.get("/jobs")
    async def list_jobs(session: AsyncSession = Depends(get_async_session)):
        ...

Usage for direct session access:
    from app.database.session import async_session_factory

    async with async_session_factory() as session:
        ...
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from app.config.settings import DatabaseType, get_settings
from app.core.logging import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# Module-level engine and session factory (initialized lazily)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Get or create the async SQLAlchemy engine.

    The engine is created lazily on first access and reused
    for the lifetime of the process.

    Returns:
        AsyncEngine: The configured async engine.
    """
    global _engine  # noqa: PLW0603

    if _engine is None:
        settings = get_settings()
        db = settings.database

        # SQLite doesn't support connection pooling
        if db.type == DatabaseType.SQLITE:
            _engine = create_async_engine(
                db.async_url,
                echo=db.echo,
                poolclass=NullPool,
                connect_args={"check_same_thread": False},
            )
        else:
            _engine = create_async_engine(
                db.async_url,
                echo=db.echo,
                poolclass=QueuePool,
                pool_size=db.pool_size,
                max_overflow=db.max_overflow,
                pool_timeout=db.pool_timeout,
                pool_pre_ping=True,
            )

        logger.info(
            "database_engine_created",
            db_type=db.type.value,
            echo=db.echo,
        )

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the async session factory.

    Returns:
        async_sessionmaker: Factory for creating async sessions.
    """
    global _session_factory  # noqa: PLW0603

    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    return _session_factory


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.

    The session is automatically committed on success and
    rolled back on exception. Always closed after use.

    Yields:
        AsyncSession: An async SQLAlchemy session.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize the database.

    Creates all tables defined in the Base metadata.
    Used for development and testing. In production,
    use Alembic migrations instead.
    """
    from app.database.base import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("database_initialized")


async def close_db() -> None:
    """
    Close the database engine and dispose of connection pool.

    Should be called during application shutdown.
    """
    global _engine, _session_factory  # noqa: PLW0603

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("database_closed")
