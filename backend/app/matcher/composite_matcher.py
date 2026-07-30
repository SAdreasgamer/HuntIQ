"""
HuntIQ — Composite Matching Engine.

Combines rule-based weighted evaluation (60%) and vector embedding semantic similarity (40%)
into a unified match score (0-100).

Persists final scores, sub-scores, missing skills, and matched resume references directly to Job records in DB.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.exceptions import RecordNotFoundError
from app.core.logging import get_logger
from app.models.job import Job
from app.matcher.job_embeddings import JobEmbeddingService
from app.matcher.rule_matcher import RuleMatchResult, RuleMatcher
from app.repositories.job import JobEmbeddingRepository, JobRepository
from app.repositories.resume import ResumeVersionRepository
from app.repositories.user import UserPreferenceRepository
from app.resume.embeddings import ResumeEmbeddingService
from app.resume.schemas import ParsedResumeData

logger = get_logger(__name__)


class CompositeMatchResult(BaseModel):
    """Output of the composite matching engine."""

    job_id: str = Field(..., description="Job primary key")
    resume_version_id: str = Field(..., description="Resume version primary key")
    composite_score: float = Field(..., description="Final composite match score (0-100)")
    rule_score: float = Field(..., description="Rule-based sub-score (0-100)")
    embedding_score: float = Field(..., description="Vector embedding similarity sub-score (0-100)")
    matched_skills: list[str] = Field(default_factory=list, description="Skills present in resume")
    missing_skills: list[str] = Field(default_factory=list, description="Skills required but missing")
    rule_breakdown: RuleMatchResult = Field(..., description="Detailed 7-dimension rule breakdown")


class MatchingEngine:
    """Production matching engine combining rules and vector embeddings."""

    def __init__(self) -> None:
        """Initialize matching engine components and config."""
        settings = get_settings()
        self.cfg = settings.matching
        self.rule_matcher = RuleMatcher()
        self.job_embed_service = JobEmbeddingService()
        self.resume_embed_service = ResumeEmbeddingService()

    async def match_job(
        self,
        session: AsyncSession,
        job_id: str,
        resume_version_id: str,
        user_id: str,
    ) -> CompositeMatchResult:
        """
        Evaluate and score a job against a specific resume version.

        Args:
            session: Async DB session.
            job_id: Job ID to evaluate.
            resume_version_id: Resume version ID.
            user_id: User owner ID.

        Returns:
            CompositeMatchResult object.
        """
        job_repo = JobRepository(session)
        resume_repo = ResumeVersionRepository(session)
        pref_repo = UserPreferenceRepository(session)
        job_embed_repo = JobEmbeddingRepository(session)

        # 1. Fetch Entities
        job = await job_repo.get_with_relations(job_id)
        if not job:
            raise RecordNotFoundError(entity="Job", identifier=job_id)

        resume_version = await resume_repo.get_with_embedding(resume_version_id)
        if not resume_version:
            raise RecordNotFoundError(entity="ResumeVersion", identifier=resume_version_id)

        user_pref = await pref_repo.get_by_user_id(user_id)

        # 2. Reconstruct ParsedResumeData schema
        parsed_resume = ParsedResumeData(**(resume_version.structured_data or {}))

        # 3. Compute Rule-Based Score (60% weight)
        rule_result = self.rule_matcher.evaluate(
            job=job,
            resume_data=parsed_resume,
            user_pref=user_pref,
            company=job.company,
        )

        # Handle blacklisted job/company immediately
        if rule_result.is_blacklisted:
            job.match_score = 0.0
            job.rule_score = 0.0
            job.embedding_score = 0.0
            await session.flush()
            return CompositeMatchResult(
                job_id=job_id,
                resume_version_id=resume_version_id,
                composite_score=0.0,
                rule_score=0.0,
                embedding_score=0.0,
                matched_skills=[],
                missing_skills=rule_result.missing_skills,
                rule_breakdown=rule_result,
            )

        # 4. Compute Embedding Similarity Score (40% weight)
        embedding_score_100 = 50.0  # default fallback if no embeddings

        # Ensure Job has embedding
        job_embed_record = await job_embed_repo.get_by_job_id(job_id)
        if not job_embed_record:
            job_embed_record = await self.job_embed_service.generate_for_job(session, job)

        # Check Resume embedding
        resume_embed_record = resume_version.embedding
        if not resume_embed_record:
            resume_embed_record = await self.resume_embed_service.create_or_update_embedding(
                session, resume_version, parsed_resume
            )

        if job_embed_record and resume_embed_record:
            sim = self.resume_embed_service.compute_cosine_similarity(
                resume_embed_record.embedding,
                job_embed_record.embedding,
            )
            embedding_score_100 = sim * 100.0

        # 5. Composite Final Score
        composite = (
            (rule_result.rule_score * self.cfg.weight_rule_score)
            + (embedding_score_100 * self.cfg.weight_embedding_score)
        )
        final_composite = round(max(0.0, min(100.0, composite)), 2)

        # 6. Update Job Record in Database
        job.match_score = final_composite
        job.rule_score = round(rule_result.rule_score, 2)
        job.embedding_score = round(embedding_score_100, 2)
        job.missing_skills = rule_result.missing_skills
        job.matched_resume_id = resume_version_id
        await session.flush()

        logger.info(
            "job_matched_successfully",
            job_id=job_id,
            composite_score=final_composite,
            rule_score=job.rule_score,
            embedding_score=job.embedding_score,
        )

        return CompositeMatchResult(
            job_id=job_id,
            resume_version_id=resume_version_id,
            composite_score=final_composite,
            rule_score=job.rule_score,
            embedding_score=job.embedding_score,
            matched_skills=rule_result.matched_skills,
            missing_skills=rule_result.missing_skills,
            rule_breakdown=rule_result,
        )

    async def batch_match_unscored_jobs(
        self,
        session: AsyncSession,
        user_id: str,
        limit: int = 50,
    ) -> list[CompositeMatchResult]:
        """
        Batch process all unscored active jobs against the user's active resume.

        Args:
            session: Async DB session.
            user_id: User ID owner.
            limit: Max jobs to process in one batch.

        Returns:
            List of CompositeMatchResult objects.
        """
        job_repo = JobRepository(session)
        resume_repo = ResumeVersionRepository(session)

        # Get user's active resume
        resume_version = await resume_repo.get_primary(user_id)
        if not resume_version:
            active_resumes = await resume_repo.get_active(user_id)
            if active_resumes:
                resume_version = active_resumes[0]

        if not resume_version:
            logger.warning("batch_match_aborted_no_active_resume", user_id=user_id)
            return []

        unscored_jobs = await job_repo.get_unscored(limit=limit)
        results: list[CompositeMatchResult] = []

        for job in unscored_jobs:
            try:
                res = await self.match_job(
                    session=session,
                    job_id=job.id,
                    resume_version_id=resume_version.id,
                    user_id=user_id,
                )
                results.append(res)
            except Exception as exc:
                logger.error("batch_job_match_failed", job_id=job.id, error=str(exc))

        await session.flush()
        logger.info(
            "batch_matching_completed",
            user_id=user_id,
            matched_count=len(results),
            limit=limit,
        )
        return results
