"""
HuntIQ — API v1 Master Router.

Combines all endpoint routers into a unified /api/v1 namespace.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics,
    applications,
    intelligence,
    jobs,
    reports,
    resumes,
    scrapers,
)

api_router = APIRouter()

api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(intelligence.router, prefix="/intelligence", tags=["Intelligence & AI"])
api_router.include_router(applications.router, prefix="/applications", tags=["Application Tracker"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(scrapers.router, prefix="/scrapers", tags=["Scrapers & Automation"])
