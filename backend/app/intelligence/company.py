"""
HuntIQ — Company Intelligence Profiler Service.

Generates deep competitive intelligence profiles for target hiring companies:
- Known engineering tech stack & infrastructure
- Engineering culture highlights & Glassdoor sentiment trends
- Typical interview process breakdown
- Recommended questions for candidates to ask interviewers

Saves output JSON directly to Company.intelligence in database.
"""

from __future__ import annotations

import hashlib
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RecordNotFoundError
from app.core.logging import get_logger
from app.llm.cache import LLMCacheService
from app.llm.chain import LLMFallbackChain
from app.llm.prompts import SYSTEM_PROMPT_COMPANY_INTELLIGENCE
from app.llm.schemas import LLMRequest, LLMTaskType
from app.repositories.company import CompanyRepository

logger = get_logger(__name__)


class CompanyIntelligenceProfile(BaseModel):
    """Structured competitive intelligence profile for a company."""

    company_name: str = Field(..., description="Company name")
    industry: str = Field(default="Technology", description="Primary industry sector")
    estimated_engineering_size: str = Field(default="100-500", description="Engineering team size estimate")
    known_tech_stack: list[str] = Field(default_factory=list, description="Core programming languages and infrastructure")
    engineering_culture_highlights: list[str] = Field(default_factory=list, description="Key work culture traits")
    interview_process_summary: str = Field(..., description="Overview of standard hiring stages")
    hiring_velocity_rating: str = Field(default="high", description="high, moderate, or low")
    pros: list[str] = Field(default_factory=list, description="Top candidate advantages")
    cons: list[str] = Field(default_factory=list, description="Potential challenges or red flags")
    recommended_questions_to_ask_interviewer: list[str] = Field(
        default_factory=list, description="Strategic questions to ask the hiring team"
    )

    model_config = {"extra": "ignore"}


class CompanyIntelligenceService:
    """Service that builds and persists company intelligence profiles."""

    def __init__(
        self,
        chain: LLMFallbackChain | None = None,
        cache_service: LLMCacheService | None = None,
    ) -> None:
        """Initialize company intelligence service."""
        self.chain = chain or LLMFallbackChain()
        self.cache_service = cache_service or LLMCacheService()

    async def profile_company(
        self,
        session: AsyncSession,
        company_id: str,
        force_refresh: bool = False,
    ) -> tuple[CompanyIntelligenceProfile, bool]:
        """
        Generate competitive intelligence profile for a company and update DB.

        Args:
            session: Async DB session.
            company_id: Primary key of company.
            force_refresh: Ignore cached profile and re-generate.

        Returns:
            Tuple of (CompanyIntelligenceProfile schema instance, is_cached_bool).
        """
        company_repo = CompanyRepository(session)
        company = await company_repo.get_by_id(company_id)
        if not company:
            raise RecordNotFoundError(entity="Company", identifier=company_id)

        content_hash = hashlib.sha256(f"company_intel:{company.name}".encode("utf-8")).hexdigest()

        prompt = f"""Generate a detailed competitive intelligence profile for the target company:

COMPANY NAME: {company.name}
DOMAIN / WEBSITE: {company.website or 'N/A'}
LOCATION / HQ: {company.headquarters or 'N/A'}
DESCRIPTION: {company.description[:1000] if company.description else 'N/A'}

Please generate a JSON object matching CompanyIntelligenceProfile with:
- "company_name": "{company.name}"
- "industry": industry sector
- "estimated_engineering_size": team size range (e.g. 50-200)
- "known_tech_stack": list of top 5 tech stack tools
- "engineering_culture_highlights": list of 3 work culture points
- "interview_process_summary": 2-sentence summary of hiring pipeline
- "hiring_velocity_rating": "high", "moderate", or "low"
- "pros": list of 3 key pros
- "cons": list of 2 potential challenges
- "recommended_questions_to_ask_interviewer": list of 3 strategic questions for interviewer
"""

        request = LLMRequest(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT_COMPANY_INTELLIGENCE,
            task_type=LLMTaskType.COMPANY_INTELLIGENCE,
            temperature=0.3,
        )

        profile, response, is_cached = await self.cache_service.execute_cached_structured(
            session=session,
            chain=self.chain,
            request=request,
            schema_cls=CompanyIntelligenceProfile,
            content_hash=content_hash,
            force_refresh=force_refresh,
        )

        # Update Company ORM model
        company.intelligence = profile.model_dump()
        if profile.known_tech_stack:
            company.tech_stack = profile.known_tech_stack
        if profile.industry and not company.industry:
            company.industry = profile.industry

        await session.flush()

        logger.info(
            "company_intelligence_profiled",
            company_id=company_id,
            company_name=company.name,
            is_cached=is_cached,
        )

        return profile, is_cached
