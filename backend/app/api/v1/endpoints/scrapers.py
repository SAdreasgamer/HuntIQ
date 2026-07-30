"""
HuntIQ — Scrapers & Automation API Endpoint.

Endpoints for triggering provider scraping runs and listing registered providers.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_stub, get_db
from app.automation.scheduler import SchedulerService
from app.models.user import User
from app.scrapers.registry import list_providers

router = APIRouter()


@router.get("/providers")
async def list_registered_providers() -> dict[str, Any]:
    """List all registered scraping providers."""
    providers = list_providers()
    return {"providers": providers, "count": len(providers)}


@router.post("/trigger")
async def trigger_scraping_run(
    title_keyword: str = Body(default="Software Engineer", embed=True),
    location: str = Body(default="Remote", embed=True),
    user: User = Depends(get_current_user_stub),
) -> dict[str, Any]:
    """Trigger immediate background scraping and matching pipeline."""
    scheduler_service = SchedulerService()
    summary = await scheduler_service.execute_scheduled_pipeline(
        user_id=user.id,
        title_keyword=title_keyword,
        location=location,
    )
    return summary
