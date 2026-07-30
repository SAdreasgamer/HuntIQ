"""
HuntIQ — Custom Exception Hierarchy.

All application-specific exceptions are defined here.
The hierarchy enables granular error handling at every layer.
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
# Database & Domain Errors
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


class InvalidStateTransitionError(HuntIQError):
    """Raised when an illegal or invalid state transition is requested."""

    def __init__(self, from_state: str, to_state: str, reason: str | None = None) -> None:
        msg = f"Cannot transition state from '{from_state}' to '{to_state}'"
        if reason:
            msg += f": {reason}"
        super().__init__(message=msg, details={"from_state": from_state, "to_state": to_state})


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


class ProviderUnavailableError(ProviderError):
    """Raised when a provider service is unavailable."""


class ProviderAuthError(ProviderError):
    """Raised when provider authentication fails."""


ProviderAuthenticationError = ProviderAuthError


# ============================================================
# Matching & Scoring Errors
# ============================================================


class MatchingError(HuntIQError):
    """Base exception for matching engine errors."""


class WeightsValidationError(MatchingError):
    """Raised when rule matcher weights do not sum to 1.0."""


class EmbeddingError(MatchingError):
    """Raised when vector embedding generation fails."""


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
