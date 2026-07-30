"""
SQLAlchemy ORM models.

This module imports all models to ensure they are registered
with the Base metadata. This is required for Alembic
autogenerate to detect all tables.

Usage:
    from app.models import User, Job, Company, Application, CoverLetter, ...
"""

# Import all models so they register with Base.metadata
from app.models.analytics import AnalyticsSnapshot
from app.models.application import Application, ApplicationStageHistory, CoverLetter
from app.models.bookmark import Bookmark, BookmarkTag
from app.models.company import Company
from app.models.job import Job, JobEmbedding, JobSkill, JobSource
from app.models.llm_cache import LLMCache
from app.models.notification import Notification
from app.models.recruiter import Recruiter
from app.models.report import Report
from app.models.resume import ResumeEmbedding, ResumeSkill, ResumeVersion
from app.models.search import SearchCheckpoint
from app.models.user import User, UserPreference


__all__ = [
    # User
    "User",
    "UserPreference",
    # Company
    "Company",
    # Job
    "Job",
    "JobSkill",
    "JobSource",
    "JobEmbedding",
    # Resume
    "ResumeVersion",
    "ResumeSkill",
    "ResumeEmbedding",
    # Application
    "Application",
    "ApplicationStageHistory",
    "CoverLetter",
    # Bookmark
    "Bookmark",
    "BookmarkTag",
    # Recruiter
    "Recruiter",
    # Notification
    "Notification",
    # Report
    "Report",
    # Analytics
    "AnalyticsSnapshot",
    # LLM Cache
    "LLMCache",
    # Search
    "SearchCheckpoint",
]
