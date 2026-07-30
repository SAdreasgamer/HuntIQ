"""
Notification repository.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Repository for Notification model operations."""

    model = Notification

    async def get_by_user(
        self,
        user_id: str,
        *,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Notification]:
        """Get notifications for a user."""
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_dedup_key(self, dedup_key: str) -> Notification | None:
        """Check if a notification with this dedup key already exists."""
        return await self.get_by_field("dedup_key", dedup_key)

    async def mark_read(self, notification_id: str) -> None:
        """Mark a notification as read."""
        await self.update(notification_id, is_read=True)

    async def mark_all_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user."""
        return await self.bulk_update(
            filters={"user_id": user_id, "is_read": False},
            values={"is_read": True},
        )

    async def get_unsent(self, limit: int = 100) -> Sequence[Notification]:
        """Get notifications that haven't been sent yet."""
        stmt = (
            select(Notification)
            .where(Notification.is_sent.is_(False))
            .order_by(Notification.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_unread(self, user_id: str) -> int:
        """Count unread notifications for a user."""
        return await self.count(filters={"user_id": user_id, "is_read": False})
