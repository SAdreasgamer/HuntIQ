"""
HuntIQ — Analytics & Aggregation Engine.

Calculates time-series snapshots for candidate job search performance:
- Total jobs discovered, high-match opportunities (>= 80% match score)
- Application conversion rates & stage distribution
- Top in-demand tech stack skills across matched jobs
- Persists snapshot history in AnalyticsSnapshot table for React charts (Recharts)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.analytics import AnalyticsSnapshot
from app.models.application import Application
from app.models.job import Job, JobSkill
from app.repositories.analytics import AnalyticsSnapshotRepository

logger = get_logger(__name__)


class AnalyticsEngineService:
    """Service for computing and aggregating job search time-series analytics."""

    async def compute_daily_snapshot(
        self,
        session: AsyncSession,
        user_id: str,
        target_date: datetime | None = None,
    ) -> AnalyticsSnapshot:
        """
        Compute and store a daily analytics snapshot for a user.

        Args:
            session: Async DB session.
            user_id: User owner ID.
            target_date: Target snapshot datetime (defaults to now UTC).

        Returns:
            Created or updated AnalyticsSnapshot ORM model.
        """
        snapshot_time = target_date or datetime.now(timezone.utc)
        analytics_repo = AnalyticsSnapshotRepository(session)

        # 1. Total Jobs in system
        total_jobs_stmt = select(func.count(Job.id))
        total_jobs_res = await session.execute(total_jobs_stmt)
        total_jobs = total_jobs_res.scalar_one() or 0

        # 2. High Match Jobs (match_score >= 80)
        high_match_stmt = select(func.count(Job.id)).where(Job.match_score >= 80.0)
        high_match_res = await session.execute(high_match_stmt)
        high_match_jobs = high_match_res.scalar_one() or 0

        # 3. Applications Count & Stage Breakdown
        app_stmt = (
            select(Application.current_stage, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.current_stage)
        )
        app_res = await session.execute(app_stmt)
        stage_counts = {row[0]: row[1] for row in app_res.all()}
        total_apps = sum(stage_counts.values())

        # 4. Top Skill Demands in Matched Jobs
        skill_stmt = (
            select(JobSkill.skill_name, func.count(JobSkill.job_id).label("cnt"))
            .group_by(JobSkill.skill_name)
            .order_by(func.count(JobSkill.job_id).desc())
            .limit(10)
        )
        skill_res = await session.execute(skill_stmt)
        top_skills = [{"skill": row[0], "count": row[1]} for row in skill_res.all()]

        interviews = stage_counts.get("interview", 0) + stage_counts.get("technical", 0)
        offers = stage_counts.get("offer", 0)

        # Check existing snapshot for today
        existing = await analytics_repo.get_by_date(snapshot_time, snapshot_type="daily")
        if existing:
            existing.total_jobs = total_jobs
            existing.high_matches = high_match_jobs
            existing.total_applications = total_apps
            existing.interviews = interviews
            existing.offers = offers
            existing.top_skills = top_skills
            snapshot = existing
        else:
            snapshot = await analytics_repo.create(
                snapshot_type="daily",
                snapshot_date=snapshot_time,
                total_jobs=total_jobs,
                high_matches=high_match_jobs,
                total_applications=total_apps,
                interviews=interviews,
                offers=offers,
                top_skills=top_skills,
            )

        await session.flush()

        logger.info(
            "analytics_snapshot_computed",
            user_id=user_id,
            snapshot_date=str(snapshot_time),
            total_jobs=total_jobs,
            total_apps=total_apps,
        )
        return snapshot

    async def get_dashboard_analytics(
        self,
        session: AsyncSession,
        user_id: str,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get aggregated dashboard analytics data for frontend charts.

        Args:
            session: Async DB session.
            user_id: User owner ID.
            days: History days limit.

        Returns:
            Dictionary of time-series data and summary cards.
        """
        analytics_repo = AnalyticsSnapshotRepository(session)
        snapshots = await analytics_repo.get_user_history(limit=days, snapshot_type="daily")

        latest_snapshot = snapshots[0] if snapshots else None

        time_series = [
            {
                "date": str(s.snapshot_date.date()) if hasattr(s.snapshot_date, "date") else str(s.snapshot_date),
                "jobs": s.total_jobs,
                "matched": s.high_matches,
                "applications": s.total_applications,
                "interviews": s.interviews,
                "offers": s.offers,
            }
            for s in reversed(snapshots)
        ]

        return {
            "summary": {
                "total_jobs": latest_snapshot.total_jobs if latest_snapshot else 0,
                "high_matches": latest_snapshot.high_matches if latest_snapshot else 0,
                "applications": latest_snapshot.total_applications if latest_snapshot else 0,
                "interviews": latest_snapshot.interviews if latest_snapshot else 0,
                "offers": latest_snapshot.offers if latest_snapshot else 0,
            },
            "time_series": time_series,
            "top_skills": latest_snapshot.top_skills if latest_snapshot else [],
        }
