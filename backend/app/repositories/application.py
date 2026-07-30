"""
Application and ApplicationStageHistory repositories.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationStageHistory
from app.repositories.base import BaseRepository


class ApplicationRepository(BaseRepository[Application]):
    """Repository for Application model operations."""

    model = Application

    async def get_with_history(self, application_id: str) -> Application | None:
        """Get an application with its stage history eagerly loaded."""
        stmt = (
            select(Application)
            .where(Application.id == application_id)
            .options(
                selectinload(Application.stage_history),
                selectinload(Application.job),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_user(
        self,
        user_id: str,
        *,
        stage: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Application]:
        """Get applications for a user, optionally filtered by stage."""
        stmt = (
            select(Application)
            .where(Application.user_id == user_id)
            .options(selectinload(Application.job))
        )
        if stage:
            stmt = stmt.where(Application.current_stage == stage)
        stmt = stmt.order_by(Application.updated_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_user_and_job(self, user_id: str, job_id: str) -> Application | None:
        """Check if a user has already applied to a specific job."""
        stmt = select(Application).where(
            Application.user_id == user_id,
            Application.job_id == job_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def transition_stage(
        self,
        application_id: str,
        new_stage: str,
        notes: str | None = None,
    ) -> Application:
        """Transition an application to a new stage and log the history."""
        application = await self.get_by_id_or_raise(application_id)
        old_stage = application.current_stage
        application.current_stage = new_stage

        # Create stage history entry
        history = ApplicationStageHistory(
            application_id=application_id,
            from_stage=old_stage,
            to_stage=new_stage,
            transitioned_at=datetime.now(timezone.utc),
            notes=notes,
        )
        self.session.add(history)
        await self.session.flush()
        await self.session.refresh(application)
        return application

    async def count_by_stage(self, user_id: str) -> list[tuple[str, int]]:
        """Get application counts grouped by stage for a user."""
        stmt = (
            select(Application.current_stage, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.current_stage)
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_upcoming_interviews(
        self,
        user_id: str,
        limit: int = 10,
    ) -> Sequence[Application]:
        """Get applications with upcoming interviews."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(Application)
            .where(
                Application.user_id == user_id,
                Application.next_interview_at.isnot(None),
                Application.next_interview_at >= now,
            )
            .options(selectinload(Application.job))
            .order_by(Application.next_interview_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ApplicationStageHistoryRepository(BaseRepository[ApplicationStageHistory]):
    """Repository for ApplicationStageHistory model operations."""

    model = ApplicationStageHistory

    async def get_by_application_id(
        self,
        application_id: str,
    ) -> Sequence[ApplicationStageHistory]:
        """Get the full stage transition history for an application."""
        stmt = (
            select(ApplicationStageHistory)
            .where(ApplicationStageHistory.application_id == application_id)
            .order_by(ApplicationStageHistory.transitioned_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
