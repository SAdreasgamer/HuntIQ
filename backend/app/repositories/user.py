"""
User and UserPreference repositories.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User, UserPreference
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""

    model = User

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by their email address."""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_with_preferences(self, user_id: str) -> User | None:
        """Get a user with their preferences eagerly loaded."""
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.preferences))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_active_users(self) -> list[User]:
        """Get all active users."""
        stmt = select(User).where(User.is_active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class UserPreferenceRepository(BaseRepository[UserPreference]):
    """Repository for UserPreference model operations."""

    model = UserPreference

    async def get_by_user_id(self, user_id: str) -> UserPreference | None:
        """Get preferences for a specific user."""
        return await self.get_by_field("user_id", user_id)

    async def upsert(self, user_id: str, **kwargs: Any) -> UserPreference:
        """Create or update user preferences."""
        existing = await self.get_by_user_id(user_id)
        if existing:
            for key, value in kwargs.items():
                setattr(existing, key, value)
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        return await self.create(user_id=user_id, **kwargs)
