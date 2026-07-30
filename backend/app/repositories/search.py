"""
SearchCheckpoint repository.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.models.search import SearchCheckpoint
from app.repositories.base import BaseRepository


class SearchCheckpointRepository(BaseRepository[SearchCheckpoint]):
    """Repository for SearchCheckpoint model operations."""

    model = SearchCheckpoint

    async def get_checkpoint(
        self,
        provider: str,
        keyword: str,
        location: str,
    ) -> SearchCheckpoint | None:
        """Get the checkpoint for a specific search combination."""
        stmt = select(SearchCheckpoint).where(
            SearchCheckpoint.provider == provider,
            SearchCheckpoint.keyword == keyword,
            SearchCheckpoint.location == location,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def upsert(
        self,
        provider: str,
        keyword: str,
        location: str,
        **kwargs: object,
    ) -> SearchCheckpoint:
        """Create or update a search checkpoint."""
        existing = await self.get_checkpoint(provider, keyword, location)
        if existing:
            for key, value in kwargs.items():
                setattr(existing, key, value)
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        return await self.create(
            provider=provider,
            keyword=keyword,
            location=location,
            **kwargs,
        )

    async def mark_complete(
        self,
        provider: str,
        keyword: str,
        location: str,
    ) -> None:
        """Mark a search as complete."""
        checkpoint = await self.get_checkpoint(provider, keyword, location)
        if checkpoint:
            checkpoint.is_complete = True
            checkpoint.completed_at = datetime.now(timezone.utc)
            await self.session.flush()

    async def get_incomplete(self, provider: str | None = None) -> list[SearchCheckpoint]:
        """Get all incomplete search checkpoints."""
        stmt = select(SearchCheckpoint).where(SearchCheckpoint.is_complete.is_(False))
        if provider:
            stmt = stmt.where(SearchCheckpoint.provider == provider)
        stmt = stmt.order_by(SearchCheckpoint.last_updated_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def reset(self, provider: str, keyword: str, location: str) -> None:
        """Reset a checkpoint to start fresh."""
        checkpoint = await self.get_checkpoint(provider, keyword, location)
        if checkpoint:
            checkpoint.last_page = 0
            checkpoint.total_results = 0
            checkpoint.is_complete = False
            checkpoint.cursor = None
            checkpoint.state_data = None
            checkpoint.error_message = None
            checkpoint.completed_at = None
            await self.session.flush()
