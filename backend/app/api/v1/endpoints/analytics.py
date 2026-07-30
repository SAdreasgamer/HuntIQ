"""
HuntIQ — Analytics API Endpoint.

Endpoints for dashboard metrics and time-series performance data.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.engine import AnalyticsEngineService
from app.api.deps import get_current_user_stub, get_db
from app.models.user import User

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_analytics(
    days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(get_current_user_stub),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get time-series analytics and KPI summary for frontend dashboard charts."""
    service = AnalyticsEngineService()
    # Ensure current snapshot is computed
    await service.compute_daily_snapshot(session, user.id)
    await session.commit()

    return await service.get_dashboard_analytics(session, user.id, days=days)
