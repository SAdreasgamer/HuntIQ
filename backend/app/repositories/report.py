"""
Report repository.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.report import Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """Repository for Report model operations."""

    model = Report

    async def get_latest(
        self,
        report_type: str | None = None,
        limit: int = 10,
    ) -> Sequence[Report]:
        """Get the most recent reports."""
        stmt = select(Report)
        if report_type:
            stmt = stmt.where(Report.report_type == report_type)
        stmt = stmt.order_by(Report.generated_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_by_type(self, report_type: str) -> Report | None:
        """Get the most recent report of a given type."""
        stmt = (
            select(Report)
            .where(Report.report_type == report_type)
            .order_by(Report.generated_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
