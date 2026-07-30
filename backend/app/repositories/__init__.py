"""
Repository layer — data access abstraction.

All database operations go through repositories.
Business logic in services should NEVER construct raw
SQLAlchemy queries — always use repository methods.

Usage:
    from app.repositories import JobRepository, CoverLetterRepository

    async def get_top_jobs(session: AsyncSession):
        repo = JobRepository(session)
        return await repo.get_top_matches(limit=10)
"""

from app.repositories.analytics import AnalyticsSnapshotRepository
from app.repositories.application import (
    ApplicationRepository,
    ApplicationStageHistoryRepository,
    CoverLetterRepository,
)
from app.repositories.base import BaseRepository
from app.repositories.bookmark import BookmarkRepository, BookmarkTagRepository
from app.repositories.company import CompanyRepository
from app.repositories.job import (
    JobEmbeddingRepository,
    JobRepository,
    JobSkillRepository,
    JobSourceRepository,
)
from app.repositories.llm_cache import LLMCacheRepository
from app.repositories.notification import NotificationRepository
from app.repositories.recruiter import RecruiterRepository
from app.repositories.report import ReportRepository
from app.repositories.resume import (
    ResumeEmbeddingRepository,
    ResumeSkillRepository,
    ResumeVersionRepository,
)
from app.repositories.search import SearchCheckpointRepository
from app.repositories.user import UserPreferenceRepository, UserRepository


__all__ = [
    # Base
    "BaseRepository",
    # User
    "UserRepository",
    "UserPreferenceRepository",
    # Company
    "CompanyRepository",
    # Job
    "JobRepository",
    "JobSkillRepository",
    "JobSourceRepository",
    "JobEmbeddingRepository",
    # Resume
    "ResumeVersionRepository",
    "ResumeSkillRepository",
    "ResumeEmbeddingRepository",
    # Application
    "ApplicationRepository",
    "ApplicationStageHistoryRepository",
    "CoverLetterRepository",
    # Bookmark
    "BookmarkRepository",
    "BookmarkTagRepository",
    # Recruiter
    "RecruiterRepository",
    # Search
    "SearchCheckpointRepository",
    # LLM Cache
    "LLMCacheRepository",
    # Notification
    "NotificationRepository",
    # Report
    "ReportRepository",
    # Analytics
    "AnalyticsSnapshotRepository",
]
