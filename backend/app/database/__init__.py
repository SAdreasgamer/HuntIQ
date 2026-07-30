"""
Database layer.

This package manages database connectivity and session lifecycle.

Usage:
    from app.database import Base, get_async_session, init_db, close_db
"""

from app.database.base import (
    Base,
    NotesMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from app.database.session import (
    close_db,
    get_async_session,
    get_engine,
    get_session_factory,
    init_db,
)


__all__ = [
    # Base
    "Base",
    # Mixins
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "SoftDeleteMixin",
    "NotesMixin",
    # Session
    "get_async_session",
    "get_engine",
    "get_session_factory",
    # Lifecycle
    "init_db",
    "close_db",
]
