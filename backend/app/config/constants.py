"""
HuntIQ — Application Constants.

Centralized constants used across the application.
These are NOT configurable via .env — they are fixed values
that define the application's behavior contracts.
"""

from __future__ import annotations

import enum


# ============================================================
# Application Stage Enum
# ============================================================


class ApplicationStage(str, enum.Enum):
    """Possible stages for a job application."""

    NOT_APPLIED = "not_applied"
    APPLIED = "applied"
    OA = "online_assessment"
    PHONE_SCREEN = "phone_screen"
    TECHNICAL_INTERVIEW = "technical_interview"
    MANAGER_ROUND = "manager_round"
    HR_ROUND = "hr_round"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


# ============================================================
# Job Source Enum
# ============================================================


class JobSourceType(str, enum.Enum):
    """Supported job source providers."""

    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    WELLFOUND = "wellfound"
    NAUKRI = "naukri"
    COMPANY_CAREERS = "company_careers"


# ============================================================
# Company Type Enum
# ============================================================


class CompanyType(str, enum.Enum):
    """Company classification types."""

    STARTUP = "startup"
    MNC = "mnc"
    MID_SIZE = "mid_size"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"
    UNKNOWN = "unknown"


# ============================================================
# Notification Type Enum
# ============================================================


class NotificationType(str, enum.Enum):
    """Types of notifications."""

    HIGH_MATCH = "high_match"
    FAVORITE_COMPANY = "favorite_company"
    NEW_JOB = "new_job"
    REPORT_READY = "report_ready"
    APPLICATION_UPDATE = "application_update"


# ============================================================
# LLM Task Type Enum
# ============================================================


class LLMTaskType(str, enum.Enum):
    """Types of LLM analysis tasks."""

    MATCH_EXPLANATION = "match_explanation"
    JOB_SUMMARY = "job_summary"
    MISSING_SKILLS = "missing_skills"
    SHORTLIST_PROBABILITY = "shortlist_probability"
    APPLY_RECOMMENDATION = "apply_recommendation"
    COVER_LETTER = "cover_letter"
    RECRUITER_MESSAGE = "recruiter_message"
    INTERVIEW_PREP = "interview_prep"
    COMPANY_SUMMARY = "company_summary"
    RESUME_IMPROVEMENTS = "resume_improvements"


# ============================================================
# Report Type Enum
# ============================================================


class ReportType(str, enum.Enum):
    """Types of generated reports."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


# ============================================================
# Bookmark Priority Enum
# ============================================================


class BookmarkPriority(str, enum.Enum):
    """Bookmark priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ============================================================
# Scoring Constants
# ============================================================

# Match score range
MIN_MATCH_SCORE: int = 0
MAX_MATCH_SCORE: int = 100

# Embedding similarity range
MIN_SIMILARITY: float = 0.0
MAX_SIMILARITY: float = 1.0

# LLM score adjustment range
MIN_LLM_ADJUSTMENT: int = -10
MAX_LLM_ADJUSTMENT: int = 10

# Deduplication similarity threshold
DEDUP_SIMILARITY_THRESHOLD: float = 0.95

# ============================================================
# API Constants
# ============================================================

# Pagination
DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100
MIN_PAGE: int = 1

# ============================================================
# Background Task Constants
# ============================================================

# Celery queue names
QUEUE_SEARCH: str = "search"
QUEUE_MATCH: str = "match"
QUEUE_LLM: str = "llm"
QUEUE_REPORT: str = "report"
QUEUE_NOTIFICATION: str = "notification"
QUEUE_MAINTENANCE: str = "maintenance"

# Task retry defaults
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_RETRY_BACKOFF: int = 60  # seconds

# ============================================================
# HTTP Constants
# ============================================================

DEFAULT_HTTP_TIMEOUT: int = 30  # seconds
DEFAULT_USER_AGENT: str = "HuntIQ/0.1.0"

# ============================================================
# Resume Constants
# ============================================================

MAX_RESUME_SIZE_MB: int = 10
ALLOWED_RESUME_EXTENSIONS: frozenset[str] = frozenset({".pdf"})
