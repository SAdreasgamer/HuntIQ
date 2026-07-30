"""
HuntIQ — API Dependencies.

FastAPI dependency injectors for DB sessions and user contexts.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session_factory
from app.models.user import User
from app.repositories.user import UserRepository


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency injecting an async SQLAlchemy session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_current_user_stub(
    session: AsyncSession = Depends(get_db),
) -> User:
    """Dependency returning a demo/primary user for development until M41 Auth."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email("demo@huntiq.io")
    if not user:
        user = await user_repo.create(
            email="demo@huntiq.io",
            hashed_password="demo_password_hash",
            full_name="HuntIQ Candidate",
        )
        await session.commit()
    return user
