"""
HuntIQ — Cover Letter Generator Service.

Generates highly tailored, high-impact cover letters using candidate resume data,
job description requirements, and customizable tones (professional, technical, conversational, executive).

Saves generated output in DB via CoverLetterRepository for editing, export, and PDF rendering.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RecordNotFoundError
from app.core.logging import get_logger
from app.llm.chain import LLMFallbackChain
from app.llm.prompts import (
    SYSTEM_PROMPT_COVER_LETTER,
    build_cover_letter_prompt,
)
from app.llm.schemas import LLMRequest, LLMTaskType
from app.models.application import CoverLetter
from app.repositories.application import CoverLetterRepository
from app.repositories.job import JobRepository
from app.repositories.resume import ResumeVersionRepository
from app.repositories.user import UserRepository
from app.resume.schemas import ParsedResumeData

logger = get_logger(__name__)


class CoverLetterGeneratorService:
    """Service that generates and persists tailored cover letters."""

    def __init__(self, chain: LLMFallbackChain | None = None) -> None:
        """Initialize cover letter generator with LLM chain."""
        self.chain = chain or LLMFallbackChain()

    async def generate_cover_letter(
        self,
        session: AsyncSession,
        user_id: str,
        job_id: str,
        resume_version_id: str,
        tone: str = "professional",
    ) -> CoverLetter:
        """
        Generate a tailored cover letter and store in DB.

        Args:
            session: Async DB session.
            user_id: User owner ID.
            job_id: Job ID to apply for.
            resume_version_id: Resume version ID used.
            tone: Desired tone ('professional', 'technical', 'conversational', 'executive').

        Returns:
            Created CoverLetter ORM model instance.
        """
        job_repo = JobRepository(session)
        resume_repo = ResumeVersionRepository(session)
        user_repo = UserRepository(session)
        cover_repo = CoverLetterRepository(session)

        # 1. Fetch Entities
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise RecordNotFoundError(entity="User", identifier=user_id)

        job = await job_repo.get_with_relations(job_id)
        if not job:
            raise RecordNotFoundError(entity="Job", identifier=job_id)

        resume_version = await resume_repo.get_by_id(resume_version_id)
        if not resume_version:
            raise RecordNotFoundError(entity="ResumeVersion", identifier=resume_version_id)

        parsed_resume = ParsedResumeData(**(resume_version.structured_data or {}))

        # Prepare highlights
        highlights = []
        for exp in parsed_resume.work_experience:
            if exp.bullet_points:
                highlights.extend(exp.bullet_points[:2])

        # 2. Build Prompt
        prompt = build_cover_letter_prompt(
            job_title=job.title,
            company_name=job.company.name if job.company else "Company",
            job_description=job.description or "",
            candidate_name=user.full_name or "Applicant",
            resume_summary=parsed_resume.summary or "",
            matched_skills=job.tech_stack or parsed_resume.skills[:5],
            work_experience_highlights=highlights if highlights else [f"Experienced in {', '.join(parsed_resume.skills[:3])}"],
            tone=tone,
        )

        request = LLMRequest(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT_COVER_LETTER,
            task_type=LLMTaskType.COVER_LETTER,
            temperature=0.7,
        )

        # 3. Generate completion via LLM chain
        response = await self.chain.generate(request)

        # 4. Save to DB via CoverLetterRepository
        cover_letter = await cover_repo.create(
            user_id=user_id,
            job_id=job_id,
            resume_version_id=resume_version_id,
            tone=tone,
            content=response.content,
            format="markdown",
            word_count=len(response.content.split()),
        )

        logger.info(
            "cover_letter_generated",
            cover_letter_id=cover_letter.id,
            user_id=user_id,
            job_id=job_id,
            word_count=cover_letter.word_count,
        )
        return cover_letter
