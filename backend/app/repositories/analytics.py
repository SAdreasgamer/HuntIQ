"""
AnalyticsSnapshot repository.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select

from app.models.analytics import AnalyticsSnapshot
from app.repositories.base import BaseRepository


class AnalyticsSnapshotRepository(BaseRepository[AnalyticsSnapshot]):
    """Repository for AnalyticsSnapshot model operations."""

    model = AnalyticsSnapshot

    async def get_latest(self, snapshot_type: str) -> AnalyticsSnapshot | None:
        """Get the most recent snapshot of a given type."""
        stmt = (
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.snapshot_type == snapshot_type)
            .order_by(AnalyticsSnapshot.snapshot_date.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_range(
        self,
        snapshot_type: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Sequence[AnalyticsSnapshot]:
        """Get snapshots within a date range."""
        stmt = (
            select(AnalyticsSnapshot)
            .where(
                AnalyticsSnapshot.snapshot_type == snapshot_type,
                AnalyticsSnapshot.snapshot_date >= start_date,
                AnalyticsSnapshot.snapshot_date <= end_date,
            )
            .order_by(AnalyticsSnapshot.snapshot_date.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_trend(
        self,
        snapshot_type: str,
        limit: int = 30,
    ) -> Sequence[AnalyticsSnapshot]:
        """Get the most recent N snapshots for trend analysis."""
        stmt = (
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.snapshot_type == snapshot_type)
            .order_by(AnalyticsSnapshot.snapshot_date.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        # Return in chronological order
        return list(reversed(result.scalars().all()))
