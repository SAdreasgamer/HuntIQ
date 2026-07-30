"""
HuntIQ — Jobs API Endpoint.

Endpoints for querying, filtering, and retrieving job opportunities.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_stub, get_db
from app.matcher.composite_matcher import MatchingEngine
from app.models.user import User
from app.repositories.job import JobRepository

router = APIRouter()


@router.get("/")
async def list_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    min_score: float | None = Query(default=None, ge=0.0, le=100.0),
    is_remote: bool | None = Query(default=None),
    location: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List active job opportunities with filtering and match score sorting."""
    job_repo = JobRepository(session)
    jobs = await job_repo.list_active(
        limit=limit,
        offset=offset,
        min_score=min_score,
        is_remote=is_remote,
        location=location,
    )

    items = []
    for j in jobs:
        items.append({
            "id": j.id,
            "title": j.title,
            "company_name": j.company.name if j.company else "N/A",
            "location": j.location,
            "is_remote": j.is_remote,
            "salary_min": j.salary_min,
            "salary_max": j.salary_max,
            "match_score": j.match_score,
            "rule_score": j.rule_score,
            "embedding_score": j.embedding_score,
            "posting_url": j.posting_url,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        })

    return {"items": items, "count": len(items), "limit": limit, "offset": offset}


@router.get("/{job_id}")
async def get_job_detail(
    job_id: str,
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get full details for a single job opportunity."""
    job_repo = JobRepository(session)
    job = await job_repo.get_with_relations(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": job.id,
        "title": job.title,
        "company": {
            "id": job.company.id if job.company else None,
            "name": job.company.name if job.company else "N/A",
            "website": job.company.website if job.company else None,
            "tech_stack": job.company.tech_stack if job.company else [],
        },
        "description": job.description,
        "requirements": job.requirements,
        "location": job.location,
        "is_remote": job.is_remote,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "match_score": job.match_score,
        "rule_score": job.rule_score,
        "embedding_score": job.embedding_score,
        "missing_skills": job.missing_skills or [],
        "explanation": job.explanation,
        "match_reasons": job.match_reasons or [],
        "posting_url": job.posting_url,
        "apply_url": job.apply_url,
    }


@router.post("/{job_id}/match")
async def trigger_job_match(
    job_id: str,
    resume_version_id: str,
    user: User = Depends(get_current_user_stub),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Trigger AI matching engine evaluation for a single job."""
    engine = MatchingEngine()
    result = await engine.match_job(
        session=session,
        job_id=job_id,
        resume_version_id=resume_version_id,
        user_id=user.id,
    )
    await session.commit()

    return {
        "job_id": result.job_id,
        "composite_score": result.composite_score,
        "rule_score": result.rule_score,
        "embedding_score": result.embedding_score,
        "matched_skills": result.matched_skills,
        "missing_skills": result.missing_skills,
    }
