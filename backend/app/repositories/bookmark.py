"""
Bookmark and BookmarkTag repositories.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.bookmark import Bookmark, BookmarkTag
from app.repositories.base import BaseRepository


class BookmarkRepository(BaseRepository[Bookmark]):
    """Repository for Bookmark model operations."""

    model = Bookmark

    async def get_by_user(
        self,
        user_id: str,
        *,
        priority: str | None = None,
        tag: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Bookmark]:
        """Get bookmarks for a user with optional filters."""
        stmt = (
            select(Bookmark)
            .where(Bookmark.user_id == user_id)
            .options(
                selectinload(Bookmark.tags),
                selectinload(Bookmark.job),
            )
        )
        if priority:
            stmt = stmt.where(Bookmark.priority == priority)
        if tag:
            stmt = stmt.join(BookmarkTag).where(BookmarkTag.tag_name == tag)
        stmt = stmt.order_by(Bookmark.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_by_user_and_job(self, user_id: str, job_id: str) -> Bookmark | None:
        """Check if a user has bookmarked a specific job."""
        stmt = select(Bookmark).where(
            Bookmark.user_id == user_id,
            Bookmark.job_id == job_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_due_reminders(self, user_id: str) -> Sequence[Bookmark]:
        """Get bookmarks with past-due reminders."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(Bookmark)
            .where(
                Bookmark.user_id == user_id,
                Bookmark.reminder_at.isnot(None),
                Bookmark.reminder_at <= now,
            )
            .options(selectinload(Bookmark.job))
            .order_by(Bookmark.reminder_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def toggle(self, user_id: str, job_id: str) -> tuple[Bookmark | None, bool]:
        """Toggle a bookmark: create if absent, delete if present. Returns (bookmark, created)."""
        existing = await self.get_by_user_and_job(user_id, job_id)
        if existing:
            await self.delete(existing.id)
            return None, False
        bookmark = await self.create(user_id=user_id, job_id=job_id)
        return bookmark, True


class BookmarkTagRepository(BaseRepository[BookmarkTag]):
    """Repository for BookmarkTag model operations."""

    model = BookmarkTag

    async def get_user_tags(self, user_id: str) -> list[str]:
        """Get all unique tag names used by a user."""
        stmt = (
            select(BookmarkTag.tag_name)
            .join(Bookmark)
            .where(Bookmark.user_id == user_id)
            .distinct()
            .order_by(BookmarkTag.tag_name)
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def add_tag(self, bookmark_id: str, tag_name: str) -> BookmarkTag:
        """Add a tag to a bookmark (idempotent)."""
        stmt = select(BookmarkTag).where(
            BookmarkTag.bookmark_id == bookmark_id,
            BookmarkTag.tag_name == tag_name,
        )
        result = await self.session.execute(stmt)
        existing = result.scalars().first()
        if existing:
            return existing
        return await self.create(bookmark_id=bookmark_id, tag_name=tag_name)
