"""
HuntIQ — Intelligence & AI Generation API Endpoint.

Endpoints for AI cover letters, recruiter messages, interview prep kits, and company profiles.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_stub, get_db
from app.intelligence.company import CompanyIntelligenceService
from app.intelligence.cover_letter import CoverLetterGeneratorService
from app.intelligence.interview_prep import InterviewPrepService
from app.intelligence.recruiter_message import RecruiterMessageGeneratorService
from app.llm.explainer import MatchExplainerService
from app.models.user import User

router = APIRouter()


@router.post("/explain-match")
async def explain_job_match(
    job_id: str = Body(..., embed=True),
    resume_version_id: str = Body(..., embed=True),
    user: User = Depends(get_current_user_stub),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate LLM AI match explanation breakdown."""
    explainer = MatchExplainerService()
    try:
        explanation = await explainer.explain_match(
            session=session,
            job_id=job_id,
            resume_version_id=resume_version_id,
            user_id=user.id,
        )
        await session.commit()
        return explanation.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Match explanation failed: {exc}")


@router.post("/cover-letter")
async def generate_cover_letter(
    job_id: str = Body(..., embed=True),
    resume_version_id: str = Body(..., embed=True),
    tone: str = Body(default="professional", embed=True),
    user: User = Depends(get_current_user_stub),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate a tailored 4-paragraph cover letter."""
    service = CoverLetterGeneratorService()
    try:
        letter = await service.generate_cover_letter(
            session=session,
            user_id=user.id,
            job_id=job_id,
            resume_version_id=resume_version_id,
            tone=tone,
        )
        await session.commit()
        return {
            "id": letter.id,
            "tone": letter.tone,
            "content": letter.content,
            "word_count": letter.word_count,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Cover letter generation failed: {exc}")


@router.post("/recruiter-message")
async def generate_recruiter_message(
    job_id: str = Body(..., embed=True),
    resume_version_id: str = Body(..., embed=True),
    recruiter_name: str | None = Body(default=None, embed=True),
    channel: str = Body(default="linkedin", embed=True),
    user: User = Depends(get_current_user_stub),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate concise recruiter outreach message."""
    service = RecruiterMessageGeneratorService()
    try:
        msg = await service.generate_outreach_message(
            session=session,
            user_id=user.id,
            job_id=job_id,
            resume_version_id=resume_version_id,
            recruiter_name=recruiter_name,
            channel=channel,
        )
        return msg.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Recruiter outreach generation failed: {exc}")


@router.post("/interview-prep")
async def generate_interview_prep(
    job_id: str = Body(..., embed=True),
    resume_version_id: str = Body(..., embed=True),
    user: User = Depends(get_current_user_stub),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate comprehensive interview prep kit."""
    service = InterviewPrepService()
    try:
        kit = await service.generate_prep_kit(
            session=session,
            user_id=user.id,
            job_id=job_id,
            resume_version_id=resume_version_id,
        )
        return kit.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Interview prep generation failed: {exc}")


@router.post("/company-profile")
async def profile_company(
    company_id: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate company intelligence profile."""
    service = CompanyIntelligenceService()
    try:
        profile = await service.profile_company(session=session, company_id=company_id)
        await session.commit()
        return profile.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Company profiling failed: {exc}")
