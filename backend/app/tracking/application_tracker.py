"""
HuntIQ — Application Tracker Service.

Manages job application lifecycles from initial bookmark to final offer or rejection.
Provides Kanban stage transitions, transition audit logging (ApplicationStageHistory),
interview scheduling, and funnel analytics.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidStateTransitionError, RecordNotFoundError
from app.core.logging import get_logger
from app.models.application import Application, ApplicationStageHistory
from app.repositories.application import ApplicationRepository
from app.repositories.job import JobRepository
from app.repositories.user import UserRepository

logger = get_logger(__name__)


class ApplicationStage(str, Enum):
    """Supported job application lifecycle stages."""

    NOT_APPLIED = "not_applied"
    BOOKMARKED = "bookmarked"
    APPLIED = "applied"
    SCREENING = "screening"
    TECHNICAL = "technical"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


VALID_STAGES = {stage.value for stage in ApplicationStage}


class ApplicationTrackerService:
    """Service managing job applications and stage transitions."""

    async def create_application(
        self,
        session: AsyncSession,
        user_id: str,
        job_id: str,
        resume_version_id: str | None = None,
        cover_letter: str | None = None,
        recruiter_name: str | None = None,
        recruiter_email: str | None = None,
        application_url: str | None = None,
        initial_stage: str = ApplicationStage.NOT_APPLIED.value,
        notes: str | None = None,
    ) -> Application:
        """Create a new job application record for tracking."""
        user_repo = UserRepository(session)
        job_repo = JobRepository(session)
        app_repo = ApplicationRepository(session)

        user = await user_repo.get_by_id(user_id)
        if not user:
            raise RecordNotFoundError(entity="User", identifier=user_id)

        job = await job_repo.get_by_id(job_id)
        if not job:
            raise RecordNotFoundError(entity="Job", identifier=job_id)

        # Check existing application
        existing = await app_repo.get_by_user_and_job(user_id, job_id)
        if existing:
            logger.info("application_already_exists", app_id=existing.id, user_id=user_id, job_id=job_id)
            return existing

        stage = initial_stage.lower()
        if stage not in VALID_STAGES:
            stage = ApplicationStage.NOT_APPLIED.value

        applied_time = datetime.now(timezone.utc) if stage == ApplicationStage.APPLIED.value else None

        application = await app_repo.create(
            user_id=user_id,
            job_id=job_id,
            current_stage=stage,
            resume_version_id=resume_version_id,
            cover_letter=cover_letter,
            recruiter_name=recruiter_name,
            recruiter_email=recruiter_email,
            application_url=application_url,
            applied_at=applied_time,
            notes=notes,
        )

        # Log initial stage history
        history = ApplicationStageHistory(
            application_id=application.id,
            from_stage=None,
            to_stage=stage,
            transitioned_at=datetime.now(timezone.utc),
            notes=f"Application created in '{stage}' stage",
        )
        session.add(history)
        await session.flush()

        logger.info(
            "application_created",
            app_id=application.id,
            user_id=user_id,
            job_id=job_id,
            stage=stage,
        )
        return application

    async def transition_stage(
        self,
        session: AsyncSession,
        application_id: str,
        new_stage: str,
        notes: str | None = None,
        next_interview_at: datetime | None = None,
        offer_amount: str | None = None,
        rejection_reason: str | None = None,
    ) -> Application:
        """Transition an application to a new stage and record audit log."""
        app_repo = ApplicationRepository(session)
        application = await app_repo.get_by_id(application_id)
        if not application:
            raise RecordNotFoundError(entity="Application", identifier=application_id)

        target_stage = new_stage.lower()
        if target_stage not in VALID_STAGES:
            raise InvalidStateTransitionError(
                from_state=application.current_stage,
                to_state=new_stage,
                reason=f"'{new_stage}' is not a valid ApplicationStage",
            )

        old_stage = application.current_stage
        application.current_stage = target_stage

        if next_interview_at is not None:
            application.next_interview_at = next_interview_at
        if offer_amount is not None:
            application.offer_amount = offer_amount
        if rejection_reason is not None:
            application.rejection_reason = rejection_reason
        if target_stage == ApplicationStage.APPLIED.value and not application.applied_at:
            application.applied_at = datetime.now(timezone.utc)

        history = ApplicationStageHistory(
            application_id=application_id,
            from_stage=old_stage,
            to_stage=target_stage,
            transitioned_at=datetime.now(timezone.utc),
            notes=notes,
        )
        session.add(history)
        await session.flush()

        logger.info(
            "application_stage_transitioned",
            app_id=application_id,
            from_stage=old_stage,
            to_stage=target_stage,
        )
        return application

    async def get_user_applications(
        self,
        session: AsyncSession,
        user_id: str,
        stage: str | None = None,
    ) -> Sequence[Application]:
        """Get all applications for a user."""
        app_repo = ApplicationRepository(session)
        return await app_repo.get_by_user(user_id, stage=stage)

    async def get_funnel_metrics(self, session: AsyncSession, user_id: str) -> dict[str, Any]:
        """Calculate application funnel analytics metrics for user dashboard."""
        app_repo = ApplicationRepository(session)
        counts_raw = await app_repo.count_by_stage(user_id)

        counts_dict = {row[0]: row[1] for row in counts_raw}
        total_apps = sum(counts_dict.values())

        applied_count = counts_dict.get(ApplicationStage.APPLIED.value, 0)
        screening_count = counts_dict.get(ApplicationStage.SCREENING.value, 0)
        interview_count = counts_dict.get(ApplicationStage.INTERVIEW.value, 0) + counts_dict.get(ApplicationStage.TECHNICAL.value, 0)
        offer_count = counts_dict.get(ApplicationStage.OFFER.value, 0)
        rejected_count = counts_dict.get(ApplicationStage.REJECTED.value, 0)

        interview_rate = (interview_count / applied_count * 100.0) if applied_count > 0 else 0.0
        offer_rate = (offer_count / applied_count * 100.0) if applied_count > 0 else 0.0

        return {
            "total_applications": total_apps,
            "applied_count": applied_count,
            "screening_count": screening_count,
            "interview_count": interview_count,
            "offer_count": offer_count,
            "rejected_count": rejected_count,
            "interview_rate_pct": round(interview_rate, 2),
            "offer_rate_pct": round(offer_rate, 2),
            "by_stage": counts_dict,
        }
