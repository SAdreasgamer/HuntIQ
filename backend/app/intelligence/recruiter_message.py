"""
HuntIQ — Recruiter Outreach Message Generator Service.

Generates high-conversion, concise outreach messages for technical recruiters
and hiring managers across LinkedIn InMail and Email channels.

Max 150 words, direct, professional, and includes low-friction call-to-action.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RecordNotFoundError
from app.core.logging import get_logger
from app.llm.chain import LLMFallbackChain
from app.llm.prompts import (
    SYSTEM_PROMPT_RECRUITER_MESSAGE,
    build_recruiter_message_prompt,
)
from app.llm.schemas import LLMRequest, LLMTaskType
from app.repositories.job import JobRepository
from app.repositories.resume import ResumeVersionRepository
from app.repositories.user import UserRepository
from app.resume.schemas import ParsedResumeData

logger = get_logger(__name__)


class RecruiterOutreachMessage(BaseModel):
    """Structured output for recruiter outreach message."""

    subject: str | None = Field(default=None, description="Email subject line if applicable")
    body: str = Field(..., description="Message body (max 150 words)")
    channel: str = Field(default="linkedin", description="linkedin or email")
    recipient_name: str = Field(..., description="Recipient name or Hiring Manager")
    call_to_action: str = Field(..., description="Closing call to action")
    word_count: int = Field(..., description="Word count of message body")

    model_config = {"extra": "ignore"}


class RecruiterMessageGeneratorService:
    """Service that generates customized recruiter outreach messages."""

    def __init__(self, chain: LLMFallbackChain | None = None) -> None:
        """Initialize message generator with LLM chain."""
        self.chain = chain or LLMFallbackChain()

    async def generate_message(
        self,
        session: AsyncSession,
        user_id: str,
        job_id: str,
        recruiter_name: str | None = None,
        channel: str = "linkedin",
    ) -> RecruiterOutreachMessage:
        """
        Generate a recruiter outreach message.

        Args:
            session: Async DB session.
            user_id: User owner ID.
            job_id: Job ID opportunity.
            recruiter_name: Recruiter or hiring manager name.
            channel: 'linkedin' or 'email'.

        Returns:
            RecruiterOutreachMessage schema instance.
        """
        job_repo = JobRepository(session)
        resume_repo = ResumeVersionRepository(session)
        user_repo = UserRepository(session)

        user = await user_repo.get_by_id(user_id)
        if not user:
            raise RecordNotFoundError(entity="User", identifier=user_id)

        job = await job_repo.get_with_relations(job_id)
        if not job:
            raise RecordNotFoundError(entity="Job", identifier=job_id)

        # Get primary resume for skills
        resume_version = await resume_repo.get_primary(user_id)
        skills = []
        if resume_version and resume_version.structured_data:
            parsed = ParsedResumeData(**resume_version.structured_data)
            skills = parsed.skills

        if not skills and job.tech_stack:
            skills = job.tech_stack if isinstance(job.tech_stack, list) else [str(job.tech_stack)]

        prompt = build_recruiter_message_prompt(
            job_title=job.title,
            company_name=job.company.name if job.company else "Company",
            recruiter_name=recruiter_name,
            candidate_name=user.full_name or "Applicant",
            key_skills=skills[:4],
            channel=channel,
        )

        request = LLMRequest(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT_RECRUITER_MESSAGE,
            task_type=LLMTaskType.RECRUITER_MESSAGE,
            temperature=0.7,
        )

        response = await self.chain.generate(request)
        content = response.content.strip()

        # Extract subject line if email channel
        subject = None
        body = content
        if channel == "email" and "subject:" in content.lower():
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if line.lower().startswith("subject:"):
                    subject = line.split(":", 1)[1].strip()
                    body = "\n".join(lines[i + 1:]).strip()
                    break

        words = body.split()
        recipient = recruiter_name or "Hiring Manager"
        cta = "Would you be open to a quick 10-minute intro call this week?"

        msg = RecruiterOutreachMessage(
            subject=subject or f"Application for {job.title} - {user.full_name}",
            body=body,
            channel=channel,
            recipient_name=recipient,
            call_to_action=cta,
            word_count=len(words),
        )

        logger.info(
            "recruiter_message_generated",
            user_id=user_id,
            job_id=job_id,
            channel=channel,
            word_count=msg.word_count,
        )
        return msg
