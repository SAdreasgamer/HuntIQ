"""
HuntIQ — Interview Preparation Kit Generator Service.

Generates comprehensive, candidate-tailored interview kits including:
- Technical deep-dive questions specific to target job requirements
- System architecture design challenges
- STAR-method behavioral questions
- Sample ideal answers and key talking points
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RecordNotFoundError
from app.core.logging import get_logger
from app.llm.cache import LLMCacheService
from app.llm.chain import LLMFallbackChain
from app.llm.prompts import SYSTEM_PROMPT_INTERVIEW_PREP
from app.llm.schemas import LLMRequest, LLMTaskType
from app.repositories.job import JobRepository
from app.repositories.resume import ResumeVersionRepository
from app.resume.schemas import ParsedResumeData

logger = get_logger(__name__)


class InterviewQuestion(BaseModel):
    """Structured representation of an interview question."""

    question: str = Field(..., description="The interview question text")
    category: str = Field(..., description="technical, system_design, behavioral, or resume_gap")
    difficulty: str = Field(default="medium", description="easy, medium, or hard")
    key_points_to_mention: list[str] = Field(default_factory=list, description="Must-include technical concepts")
    sample_star_answer: str | None = Field(default=None, description="Sample STAR-method response")

    model_config = {"extra": "ignore"}


class InterviewPrepKit(BaseModel):
    """Structured output for complete interview preparation kit."""

    job_title: str = Field(..., description="Target job title")
    company_name: str = Field(..., description="Target company name")
    technical_questions: list[InterviewQuestion] = Field(default_factory=list, description="Technical questions")
    behavioral_questions: list[InterviewQuestion] = Field(default_factory=list, description="Behavioral questions")
    system_design_questions: list[InterviewQuestion] = Field(default_factory=list, description="Architecture questions")
    top_preparation_tips: list[str] = Field(default_factory=list, description="Actionable interview tips")

    model_config = {"extra": "ignore"}


class InterviewPrepService:
    """Service that generates candidate-tailored interview prep kits."""

    def __init__(
        self,
        chain: LLMFallbackChain | None = None,
        cache_service: LLMCacheService | None = None,
    ) -> None:
        """Initialize prep service with LLM chain and cache service."""
        self.chain = chain or LLMFallbackChain()
        self.cache_service = cache_service or LLMCacheService()

    async def generate_prep_kit(
        self,
        session: AsyncSession,
        user_id: str,
        job_id: str,
        resume_version_id: str | None = None,
        force_refresh: bool = False,
    ) -> tuple[InterviewPrepKit, bool]:
        """
        Generate tailored interview preparation kit.

        Args:
            session: Async DB session.
            user_id: User owner ID.
            job_id: Job opportunity ID.
            resume_version_id: Optional resume version ID.
            force_refresh: Ignore cache and re-generate.

        Returns:
            Tuple of (InterviewPrepKit schema instance, is_cached_bool).
        """
        job_repo = JobRepository(session)
        resume_repo = ResumeVersionRepository(session)

        job = await job_repo.get_with_relations(job_id)
        if not job:
            raise RecordNotFoundError(entity="Job", identifier=job_id)

        # Get resume
        if resume_version_id:
            resume_version = await resume_repo.get_by_id(resume_version_id)
        else:
            resume_version = await resume_repo.get_primary(user_id)

        resume_version_id_str = resume_version.id if resume_version else None
        skills_str = "Software Engineering"
        summary_str = ""

        if resume_version and resume_version.structured_data:
            parsed = ParsedResumeData(**resume_version.structured_data)
            skills_str = ", ".join(parsed.skills)
            summary_str = parsed.summary or ""

        company_name = job.company.name if job.company else "Company"

        prompt = f"""Generate a comprehensive interview prep kit for the candidate and job opportunity:

TARGET ROLE: {job.title}
TARGET COMPANY: {company_name}
JOB DESCRIPTION:
{job.description[:1500] if job.description else 'N/A'}

CANDIDATE SKILLS: {skills_str}
CANDIDATE SUMMARY: {summary_str}

Please generate a JSON object matching the InterviewPrepKit schema with:
- "job_title": "{job.title}"
- "company_name": "{company_name}"
- "technical_questions": list of 3 InterviewQuestion objects (technical deep dives)
- "behavioral_questions": list of 2 InterviewQuestion objects (STAR method)
- "system_design_questions": list of 2 InterviewQuestion objects (architecture)
- "top_preparation_tips": list of 3 strategic preparation tips
"""

        request = LLMRequest(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT_INTERVIEW_PREP,
            task_type=LLMTaskType.INTERVIEW_PREP,
            temperature=0.4,
        )

        kit, response, is_cached = await self.cache_service.execute_cached_structured(
            session=session,
            chain=self.chain,
            request=request,
            schema_cls=InterviewPrepKit,
            content_hash=job.content_hash,
            resume_version_id=resume_version_id_str,
            force_refresh=force_refresh,
        )

        logger.info(
            "interview_prep_kit_generated",
            job_id=job_id,
            user_id=user_id,
            tech_q_count=len(kit.technical_questions),
            is_cached=is_cached,
        )

        return kit, is_cached
