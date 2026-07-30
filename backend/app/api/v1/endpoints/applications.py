"""
HuntIQ — Application Tracker API Endpoint.

Endpoints for Kanban stage transitions, application management, and stage history logs.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_stub, get_db
from app.models.user import User
from app.tracking.application_tracker import ApplicationTrackerService

router = APIRouter()


@router.get("/")
async def list_applications(
    user: User = Depends(get_current_user_stub),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get candidate application Kanban list and stage distribution."""
    service = ApplicationTrackerService()
    apps = await service.get_user_applications(session, user.id)

    items = [
        {
            "id": a.id,
            "job_id": a.job_id,
            "job_title": a.job.title if a.job else "N/A",
            "company_name": a.job.company.name if (a.job and a.job.company) else "N/A",
            "current_stage": a.current_stage,
            "applied_at": a.applied_at.isoformat() if a.applied_at else None,
            "recruiter_name": a.recruiter_name,
            "recruiter_email": a.recruiter_email,
            "next_interview_at": a.next_interview_at.isoformat() if a.next_interview_at else None,
            "offer_amount": a.offer_amount,
        }
        for a in apps
    ]
    return {"items": items, "count": len(items)}


@router.post("/")
async def create_application(
    job_id: str = Body(..., embed=True),
    current_stage: str = Body(default="bookmarked", embed=True),
    user: User = Depends(get_current_user_stub),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new job application tracking record."""
    service = ApplicationTrackerService()
    app = await service.create_application(session, user.id, job_id, initial_stage=current_stage)
    await session.commit()
    return {
        "id": app.id,
        "job_id": app.job_id,
        "current_stage": app.current_stage,
    }


@router.put("/{application_id}/stage")
async def update_application_stage(
    application_id: str,
    new_stage: str = Body(..., embed=True),
    notes: str | None = Body(default=None, embed=True),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Transition an application to a new Kanban stage."""
    service = ApplicationTrackerService()
    try:
        app = await service.transition_stage(session, application_id, new_stage=new_stage, notes=notes)
        await session.commit()
        return {
            "id": app.id,
            "current_stage": app.current_stage,
            "updated_at": app.updated_at.isoformat() if app.updated_at else None,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
