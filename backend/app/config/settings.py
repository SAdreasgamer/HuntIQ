"""
HuntIQ — Centralized Configuration Management.

All application configuration is loaded from environment variables
and .env files via Pydantic Settings. No other module should read
environment variables directly — always import from here.

Usage:
    from app.config.settings import get_settings

    settings = get_settings()
    print(settings.database.url)
"""

from __future__ import annotations

import enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ============================================================
# Path Constants
# ============================================================

# Root of the backend/ directory
BACKEND_DIR: Path = Path(__file__).resolve().parent.parent.parent
# Root of the project (one level above backend/)
PROJECT_ROOT: Path = BACKEND_DIR.parent
# Default .env file location
ENV_FILE: Path = PROJECT_ROOT / ".env"


# ============================================================
# Enums
# ============================================================


class Environment(str, enum.Enum):
    """Application environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseType(str, enum.Enum):
    """Supported database backends."""

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


class LLMProviderType(str, enum.Enum):
    """Supported LLM providers."""

    OPENROUTER = "openrouter"
    OPENAI = "openai"
    OLLAMA = "ollama"


class LogLevel(str, enum.Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ============================================================
# Sub-Settings: Database
# ============================================================


class DatabaseSettings(BaseSettings):
    """Database connection configuration."""

    model_config = SettingsConfigDict(env_prefix="DB_")

    type: DatabaseType = Field(
        default=DatabaseType.SQLITE,
        description="Database backend: sqlite or postgresql",
    )
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="huntiq", description="Database name")
    user: str = Field(default="huntiq", description="Database user")
    password: SecretStr = Field(default=SecretStr(""), description="Database password")
    echo: bool = Field(default=False, description="Echo SQL statements to log")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max connections above pool_size")
    pool_timeout: int = Field(default=30, description="Seconds to wait for a connection")
    sqlite_path: str = Field(
        default="huntiq.db",
        description="SQLite database file path (relative to project root)",
    )

    @property
    def async_url(self) -> str:
        """Build the async database URL."""
        if self.type == DatabaseType.SQLITE:
            db_path = PROJECT_ROOT / self.sqlite_path
            return f"sqlite+aiosqlite:///{db_path}"
        password = self.password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.user}:{password}"
            f"@{self.host}:{self.port}/{self.name}"
        )

    @property
    def sync_url(self) -> str:
        """Build the sync database URL (for Alembic migrations)."""
        if self.type == DatabaseType.SQLITE:
            db_path = PROJECT_ROOT / self.sqlite_path
            return f"sqlite:///{db_path}"
        password = self.password.get_secret_value()
        return (
            f"postgresql+psycopg2://{self.user}:{password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


# ============================================================
# Sub-Settings: Redis
# ============================================================


class RedisSettings(BaseSettings):
    """Redis connection configuration."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    ttl: int = Field(default=3600, description="Default cache TTL in seconds")
    max_connections: int = Field(default=10, description="Max Redis connections")
    key_prefix: str = Field(default="huntiq:", description="Key prefix for namespacing")


# ============================================================
# Sub-Settings: Apify
# ============================================================


class ApifySettings(BaseSettings):
    """Apify API configuration."""

    model_config = SettingsConfigDict(env_prefix="APIFY_")

    token: SecretStr = Field(default=SecretStr(""), description="Apify API token")
    base_url: str = Field(
        default="https://api.apify.com/v2",
        description="Apify API base URL",
    )
    default_timeout: int = Field(default=300, description="Default actor run timeout in seconds")
    max_retries: int = Field(default=3, description="Max retries for failed actor runs")
    memory_mbytes: int = Field(default=256, description="Memory allocation per actor run in MB")


# ============================================================
# Sub-Settings: LLM
# ============================================================


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    model_config = SettingsConfigDict(env_prefix="LLM_")

    provider: LLMProviderType = Field(
        default=LLMProviderType.OPENROUTER,
        description="Primary LLM provider",
    )
    model: str = Field(
        default="meta-llama/llama-3.1-8b-instruct:free",
        description="Primary LLM model identifier",
    )
    api_key: SecretStr = Field(default=SecretStr(""), description="LLM provider API key")
    base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="LLM provider base URL",
    )
    temperature: float = Field(default=0.3, description="LLM temperature for generation")
    max_tokens: int = Field(default=2048, description="Max tokens per LLM response")
    timeout: int = Field(default=60, description="LLM request timeout in seconds")

    # Fallback configuration
    fallback_provider: LLMProviderType | None = Field(
        default=None,
        description="Fallback LLM provider if primary fails",
    )
    fallback_model: str = Field(
        default="",
        description="Fallback LLM model identifier",
    )
    fallback_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Fallback LLM provider API key",
    )
    fallback_base_url: str = Field(
        default="",
        description="Fallback LLM provider base URL",
    )

    # Caching
    cache_enabled: bool = Field(default=True, description="Enable LLM response caching")
    cache_ttl: int = Field(default=86400 * 7, description="LLM cache TTL in seconds (7 days)")

    # Rate limiting
    requests_per_minute: int = Field(default=20, description="Max LLM requests per minute")

    # Quality gate
    min_score_for_llm: int = Field(
        default=40,
        description="Minimum combined rule+embedding score to trigger LLM analysis",
    )


# ============================================================
# Sub-Settings: Search
# ============================================================


class SearchSettings(BaseSettings):
    """Job search configuration."""

    model_config = SettingsConfigDict(env_prefix="SEARCH_")

    keywords: list[str] = Field(
        default=[
            "Backend Engineer",
            "Software Engineer",
            "Backend Software Engineer",
            "Java Developer",
            "Platform Engineer",
            "SDE-1",
            "Associate Software Engineer",
            "Graduate Software Engineer",
            "Microservices Engineer",
            "Distributed Systems Engineer",
            "Server Side Engineer",
        ],
        description="Job search keywords",
    )
    locations: list[str] = Field(
        default=[
            "India",
            "Remote",
            "Singapore",
            "Germany",
            "Netherlands",
            "Ireland",
            "United Kingdom",
        ],
        description="Job search locations",
    )
    excluded_keywords: list[str] = Field(
        default=[
            "Frontend",
            "React",
            "Angular",
            "Flutter",
            "Android",
            "iOS",
            "QA",
            "Manual Testing",
            "Prompt Engineer",
            "Business Analyst",
            "Support Engineer",
            "SAP",
            "Salesforce",
            "ML Research",
            "Data Scientist",
        ],
        description="Keywords to filter out from results",
    )
    frequency_hours: int = Field(default=6, description="Hours between automatic searches")
    max_results_per_provider: int = Field(
        default=100,
        description="Max results to fetch per provider per search",
    )
    concurrent_providers: int = Field(
        default=4,
        description="Max number of providers to search concurrently",
    )
    max_retries: int = Field(default=3, description="Max retries per search request")
    retry_backoff_base: float = Field(
        default=2.0,
        description="Exponential backoff base for retries (seconds)",
    )

    @field_validator("keywords", "locations", "excluded_keywords", mode="before")
    @classmethod
    def parse_comma_separated(cls, v: Any) -> list[str]:
        """Accept comma-separated strings from .env as lists."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v


# ============================================================
# Sub-Settings: Matching
# ============================================================


class MatchingSettings(BaseSettings):
    """Matching engine configuration."""

    model_config = SettingsConfigDict(env_prefix="MATCH_")

    notification_threshold: int = Field(
        default=60,
        description="Minimum match score to trigger notification (0-100)",
    )
    llm_threshold: int = Field(
        default=40,
        description="Minimum combined score to trigger LLM analysis (0-100)",
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings",
    )
    embedding_dimensions: int = Field(
        default=384,
        description="Embedding vector dimensions",
    )

    # Scoring weights (must sum to 1.0)
    weight_skills: float = Field(default=0.25, description="Weight for skills match")
    weight_role: float = Field(default=0.20, description="Weight for role match")
    weight_experience: float = Field(default=0.15, description="Weight for experience match")
    weight_tech_stack: float = Field(default=0.15, description="Weight for tech stack match")
    weight_keywords: float = Field(default=0.10, description="Weight for keyword match")
    weight_location: float = Field(default=0.10, description="Weight for location match")
    weight_company_pref: float = Field(default=0.05, description="Weight for company preference")

    # Final score composition
    weight_rule_score: float = Field(default=0.6, description="Weight of rule-based score")
    weight_embedding_score: float = Field(default=0.4, description="Weight of embedding score")

    @model_validator(mode="after")
    def validate_weights(self) -> "MatchingSettings":
        """Validate that scoring weights sum to approximately 1.0."""
        component_sum = (
            self.weight_skills
            + self.weight_role
            + self.weight_experience
            + self.weight_tech_stack
            + self.weight_keywords
            + self.weight_location
            + self.weight_company_pref
        )
        if abs(component_sum - 1.0) > 0.01:
            msg = f"Component scoring weights must sum to 1.0, got {component_sum:.2f}"
            raise ValueError(msg)

        final_sum = self.weight_rule_score + self.weight_embedding_score
        if abs(final_sum - 1.0) > 0.01:
            msg = f"Final score weights must sum to 1.0, got {final_sum:.2f}"
            raise ValueError(msg)

        return self


# ============================================================
# Sub-Settings: Notification
# ============================================================


class NotificationSettings(BaseSettings):
    """Notification delivery configuration."""

    model_config = SettingsConfigDict(env_prefix="NOTIFY_")

    enabled: bool = Field(default=True, description="Enable notifications globally")

    # Email
    email_enabled: bool = Field(default=False, description="Enable email notifications")
    email_to: str = Field(default="", description="Recipient email address")
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_user: str = Field(default="", description="SMTP username")
    smtp_password: SecretStr = Field(default=SecretStr(""), description="SMTP password")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")

    # Desktop
    desktop_enabled: bool = Field(default=True, description="Enable desktop notifications")

    # Webhook
    webhook_enabled: bool = Field(default=False, description="Enable webhook notifications")
    webhook_url: str = Field(default="", description="Webhook endpoint URL")
    webhook_secret: SecretStr = Field(default=SecretStr(""), description="Webhook signing secret")

    # Rules
    min_score: int = Field(default=60, description="Minimum score to notify")
    notify_favorites_only: bool = Field(
        default=False,
        description="Only notify for favorite companies",
    )
    max_age_hours: int = Field(default=48, description="Max job age in hours to notify")


# ============================================================
# Sub-Settings: Security
# ============================================================


class SecuritySettings(BaseSettings):
    """Security and authentication configuration."""

    model_config = SettingsConfigDict(env_prefix="SECURITY_")

    secret_key: SecretStr = Field(
        default=SecretStr("CHANGE-ME-IN-PRODUCTION-use-openssl-rand-hex-32"),
        description="JWT signing secret key",
    )
    algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiry in minutes",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiry in days",
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:8000", "http://localhost:3000"],
        description="Allowed CORS origins",
    )
    rate_limit_per_minute: int = Field(
        default=60,
        description="API rate limit per minute per user",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Accept comma-separated strings from .env as lists."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


# ============================================================
# Root Settings
# ============================================================


class Settings(BaseSettings):
    """
    Root application settings.

    All configuration is loaded from environment variables and the .env file.
    Sub-settings are nested for logical grouping.
    """

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="HuntIQ", description="Application name")
    app_env: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment",
    )
    debug: bool = Field(default=True, description="Enable debug mode")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    host: str = Field(default="0.0.0.0", description="Server bind host")
    port: int = Field(default=8000, description="Server bind port")

    # Sub-settings (loaded independently with their own env prefixes)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    apify: ApifySettings = Field(default_factory=ApifySettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    search: SearchSettings = Field(default_factory=SearchSettings)
    matching: MatchingSettings = Field(default_factory=MatchingSettings)
    notification: NotificationSettings = Field(default_factory=NotificationSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == Environment.PRODUCTION


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached application settings singleton.

    Settings are loaded once and cached for the lifetime of the process.
    To reload, call get_settings.cache_clear() first.

    Returns:
        Settings: The application settings instance.
    """
    return Settings()
