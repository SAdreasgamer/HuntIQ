"""
Configuration management.

This package contains Pydantic Settings classes that load
and validate all application configuration from environment
variables and .env files.

All configuration is centralized here. No other module
should read environment variables directly.

Usage:
    from app.config import get_settings

    settings = get_settings()
"""

from app.config.constants import (
    ApplicationStage,
    BookmarkPriority,
    CompanyType,
    JobSourceType,
    LLMTaskType,
    NotificationType,
    ReportType,
)
from app.config.settings import (
    DatabaseType,
    Environment,
    LLMProviderType,
    LogLevel,
    Settings,
    get_settings,
)


__all__ = [
    # Settings
    "Settings",
    "get_settings",
    # Enums (settings)
    "Environment",
    "DatabaseType",
    "LLMProviderType",
    "LogLevel",
    # Enums (constants)
    "ApplicationStage",
    "BookmarkPriority",
    "CompanyType",
    "JobSourceType",
    "LLMTaskType",
    "NotificationType",
    "ReportType",
]
