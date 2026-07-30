"""
HuntIQ — Custom Exception Hierarchy.

All application-specific exceptions are defined here.
The hierarchy enables granular error handling at every layer.

Base: HuntIQError
├── ConfigurationError
├── DatabaseError
├── ProviderError
│   ├── ProviderTimeoutError
│   ├── ProviderRateLimitError
│   └── ProviderUnavailableError
├── MatchingError
├── ResumeParsingError
├── LLMError
│   ├── LLMTimeoutError
│   ├── LLMRateLimitError
│   └── LLMUnavailableError
├── NotificationError
├── ReportError
├── AuthenticationError
├── AuthorizationError
└── ValidationError
"""

from __future__ import annotations


class HuntIQError(Exception):
    """Base exception for all HuntIQ application errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, details={self.details!r})"


# ============================================================
# Configuration Errors
# ============================================================


class ConfigurationError(HuntIQError):
    """Raised when application configuration is invalid or missing."""


# ============================================================
# Database Errors
# ============================================================


class DatabaseError(HuntIQError):
    """Raised when a database operation fails."""


class RecordNotFoundError(DatabaseError):
    """Raised when a requested record does not exist."""

    def __init__(self, entity: str, identifier: str | int) -> None:
        super().__init__(
            message=f"{entity} with identifier '{identifier}' not found",
            details={"entity": entity, "identifier": str(identifier)},
        )


class DuplicateRecordError(DatabaseError):
    """Raised when attempting to create a record that already exists."""

    def __init__(self, entity: str, field: str, value: str) -> None:
        super().__init__(
            message=f"{entity} with {field}='{value}' already exists",
            details={"entity": entity, "field": field, "value": value},
        )


# ============================================================
# Provider Errors (Job Scrapers)
# ============================================================


class ProviderError(HuntIQError):
    """Base exception for job provider errors."""

    def __init__(self, provider: str, message: str, details: dict | None = None) -> None:
        self.provider = provider
        super().__init__(
            message=f"[{provider}] {message}",
            details={"provider": provider, **(details or {})},
        )


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request times out."""


class ProviderRateLimitError(ProviderError):
    """Raised when a provider rate limit is exceeded."""

    def __init__(self, provider: str, retry_after: int | None = None) -> None:
        self.retry_after = retry_after
        super().__init__(
            provider=provider,
            message=f"Rate limit exceeded. Retry after {retry_after}s"
            if retry_after
            else "Rate limit exceeded",
            details={"retry_after": retry_after},
        )


class ProviderUnavailableError(ProviderError):
    """Raised when a provider is temporarily unavailable."""


class ProviderAuthenticationError(ProviderError):
    """Raised when provider authentication fails (bad API key, etc)."""


# ============================================================
# Matching Errors
# ============================================================


class MatchingError(HuntIQError):
    """Raised when the matching engine encounters an error."""


class EmbeddingError(MatchingError):
    """Raised when embedding generation or comparison fails."""


# ============================================================
# Resume Errors
# ============================================================


class ResumeError(HuntIQError):
    """Base exception for resume processing errors."""


class ResumeParsingError(ResumeError):
    """Raised when resume PDF parsing fails."""

    def __init__(self, filename: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to parse resume '{filename}': {reason}",
            details={"filename": filename, "reason": reason},
        )


class ResumeValidationError(ResumeError):
    """Raised when a parsed resume fails validation checks."""


# ============================================================
# LLM Errors
# ============================================================


class LLMError(HuntIQError):
    """Base exception for LLM service errors."""

    def __init__(self, provider: str, message: str, details: dict | None = None) -> None:
        self.provider = provider
        super().__init__(
            message=f"[LLM:{provider}] {message}",
            details={"provider": provider, **(details or {})},
        )


class LLMTimeoutError(LLMError):
    """Raised when an LLM request times out."""


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""


class LLMUnavailableError(LLMError):
    """Raised when the LLM provider is unavailable."""


class LLMResponseError(LLMError):
    """Raised when the LLM response cannot be parsed or is invalid."""


# ============================================================
# Notification Errors
# ============================================================


class NotificationError(HuntIQError):
    """Raised when notification delivery fails."""

    def __init__(self, channel: str, message: str, details: dict | None = None) -> None:
        self.channel = channel
        super().__init__(
            message=f"[{channel}] {message}",
            details={"channel": channel, **(details or {})},
        )


# ============================================================
# Report Errors
# ============================================================


class ReportError(HuntIQError):
    """Raised when report generation fails."""


# ============================================================
# Authentication & Authorization Errors
# ============================================================


class AuthenticationError(HuntIQError):
    """Raised when authentication fails."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""

    def __init__(self) -> None:
        super().__init__(message="Invalid email or password")


class TokenExpiredError(AuthenticationError):
    """Raised when a JWT token has expired."""

    def __init__(self) -> None:
        super().__init__(message="Token has expired")


class InvalidTokenError(AuthenticationError):
    """Raised when a JWT token is malformed or invalid."""

    def __init__(self) -> None:
        super().__init__(message="Invalid or malformed token")


class AuthorizationError(HuntIQError):
    """Raised when a user lacks permission for an operation."""

    def __init__(self, action: str, resource: str) -> None:
        super().__init__(
            message=f"Not authorized to {action} on {resource}",
            details={"action": action, "resource": resource},
        )


# ============================================================
# Validation Errors
# ============================================================


class AppValidationError(HuntIQError):
    """Raised when business-level validation fails (not Pydantic)."""
