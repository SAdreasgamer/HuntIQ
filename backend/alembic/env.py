"""
Alembic environment configuration.

This file is executed by Alembic to configure the migration
environment. It supports both online (connected to DB) and
offline (SQL script generation) migration modes.

Key features:
- Loads database URL from app settings (.env)
- Imports all models to populate Base.metadata
- Supports async engine for migrations
- Renders JSON/dict columns as sa.JSON
"""

from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Add the backend directory to sys.path so we can import app modules
backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import the Base metadata (this triggers all model registration)
from app.database.base import Base  # noqa: E402

# Import all models so their tables are registered with Base.metadata
import app.models  # noqa: E402, F401

# Import settings to get the database URL
from app.config.settings import get_settings  # noqa: E402

# Alembic Config object (provides access to alembic.ini values)
config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata

# Load the database URL from our app settings
settings = get_settings()
database_url = settings.database.async_url

# Override the sqlalchemy.url in alembic config
config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    Useful for reviewing migrations before applying them.
    """
    url = config.get_main_option("sqlalchemy.url")

    # For offline mode with async URLs, convert to sync
    if url and "+aiosqlite" in url:
        url = url.replace("sqlite+aiosqlite", "sqlite")
    elif url and "+asyncpg" in url:
        url = url.replace("postgresql+asyncpg", "postgresql")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations with a live database connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations using an async engine.

    Creates an async engine from the alembic config,
    connects, and runs migrations synchronously within
    the connection context.
    """
    configuration = config.get_section(config.config_ini_section, {})

    # Convert async URL to format needed by create_async_engine
    url = configuration.get("sqlalchemy.url", database_url)
    configuration["sqlalchemy.url"] = url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Connects to the database and applies migrations directly.
    Uses async engine for compatibility with our async setup.
    """
    asyncio.run(run_async_migrations())


# Determine which mode to run in
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
