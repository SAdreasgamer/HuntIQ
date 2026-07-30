"""
LLMCache ORM model.

Caches LLM responses to avoid redundant API calls.
Keyed by (job content hash, task type, resume version).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin


class LLMCache(Base, UUIDPrimaryKeyMixin):
    """Cached LLM response to avoid reprocessing."""

    __tablename__ = "llm_caches"
    __table_args__ = (
        UniqueConstraint(
            "content_hash",
            "task_type",
            "resume_version_id",
            name="uq_llm_cache_key",
        ),
    )

    # Cache key components
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="SHA-256 hash of the job/content being analyzed",
    )
    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="LLM task type: match_explanation, job_summary, etc.",
    )
    resume_version_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        default=None,
        doc="Resume version ID (null for resume-independent tasks)",
    )

    # LLM request/response
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="LLM provider used: openrouter, openai, ollama",
    )
    model: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="LLM model used",
    )
    prompt_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Hash of the prompt sent to the LLM",
    )
    response_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Raw LLM response text",
    )
    response_structured: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Parsed/structured LLM response",
    )

    # Usage tracking
    prompt_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        doc="Number of prompt tokens used",
    )
    completion_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        doc="Number of completion tokens generated",
    )
    total_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        doc="Total tokens used",
    )
    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        doc="Response latency in milliseconds",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When this cache entry was created",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="When this cache entry expires",
    )
