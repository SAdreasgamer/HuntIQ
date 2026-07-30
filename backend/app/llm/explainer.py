"""
HuntIQ — AI Match Explanation Service.

Generates deep AI candidate match analysis, executive summaries, shortlist probability,
skill gap analysis, and tailored application advice for job listings.

Saves explanation JSON directly to Job.explanation in database.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RecordNotFoundError
from app.core.logging import get_logger
from app.llm.cache import LLMCacheService
from app.llm.chain import LLMFallbackChain
from app.llm.prompts import (
    SYSTEM_PROMPT_MATCH_EXPLAINER,
    build_match_explanation_prompt,
)
from app.llm.schemas import (
    AIJobMatchExplanation,
    LLMRequest,
    LLMTaskType,
)
from app.models.job import Job
from app.models.resume import ResumeVersion
from app.repositories.job import JobRepository
from app.repositories.resume import ResumeVersionRepository
from app.resume.schemas import ParsedResumeData

logger = get_logger(__name__)


class MatchExplainerService:
    """Service that coordinates AI Match Explanation generation and DB persistence."""

    def __init__(
        self,
        chain: LLMFallbackChain | None = None,
        cache_service: LLMCacheService | None = None,
    ) -> None:
        """Initialize explainer service with LLM chain and cache service."""
        self.chain = chain or LLMFallbackChain()
        self.cache_service = cache_service or LLMCacheService()

    async def explain_job_match(
        self,
        session: AsyncSession,
        job_id: str,
        resume_version_id: str,
        force_refresh: bool = False,
    ) -> tuple[AIJobMatchExplanation, bool]:
        """
        Generate AI match explanation for a job listing and save output in DB.

        Args:
            session: Async DB session.
            job_id: Job primary key.
            resume_version_id: Resume version primary key.
            force_refresh: Ignore cached explanation and re-generate.

        Returns:
            Tuple of (AIJobMatchExplanation Pydantic model, is_cached_boolean).
        """
        job_repo = JobRepository(session)
        resume_repo = ResumeVersionRepository(session)

        # Fetch Entities
        job = await job_repo.get_with_relations(job_id)
        if not job:
            raise RecordNotFoundError(entity="Job", identifier=job_id)

        resume_version = await resume_repo.get_by_id(resume_version_id)
        if not resume_version:
            raise RecordNotFoundError(entity="ResumeVersion", identifier=resume_version_id)

        parsed_resume = ParsedResumeData(**(resume_version.structured_data or {}))

        # Build prompt
        prompt = build_match_explanation_prompt(
            job_title=job.title,
            company_name=job.company.name if job.company else "Company",
            job_description=job.description or "",
            resume_summary=parsed_resume.summary or "",
            resume_skills=parsed_resume.skills,
            experience_years=parsed_resume.total_experience_years,
            rule_score=job.rule_score or 50.0,
            embedding_score=job.embedding_score or 50.0,
        )

        request = LLMRequest(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT_MATCH_EXPLAINER,
            task_type=LLMTaskType.MATCH_EXPLANATION,
            temperature=0.3,
        )

        # Execute via Cache + Chain
        explanation, response, is_cached = await self.cache_service.execute_cached_structured(
            session=session,
            chain=self.chain,
            request=request,
            schema_cls=AIJobMatchExplanation,
            content_hash=job.content_hash,
            resume_version_id=resume_version_id,
            force_refresh=force_refresh,
        )

        # Update Job ORM fields
        job.explanation = explanation.model_dump()
        job.match_reasons = explanation.key_strengths
        await session.flush()

        logger.info(
            "job_match_explained_successfully",
            job_id=job_id,
            shortlist_prob=explanation.shortlist_probability,
            is_cached=is_cached,
        )

        return explanation, is_cached
