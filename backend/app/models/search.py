"""
SearchCheckpoint ORM model.

Enables resuming interrupted searches by saving progress
state per (provider, keyword, location) combination.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin


class SearchCheckpoint(Base, UUIDPrimaryKeyMixin):
    """Search progress checkpoint for resumable searches."""

    __tablename__ = "search_checkpoints"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "keyword",
            "location",
            name="uq_search_checkpoint",
        ),
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Provider name: linkedin, greenhouse, etc.",
    )
    keyword: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Search keyword used",
    )
    location: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Search location used",
    )

    # Progress state
    last_page: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Last successfully processed page number",
    )
    total_results: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total results found so far",
    )
    is_complete: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this search has been fully completed",
    )

    # State data
    cursor: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        default=None,
        doc="Pagination cursor/token for the next page",
    )
    state_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Provider-specific checkpoint state data",
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        default=None,
        doc="Last error message if search failed",
    )

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="When this search was started",
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="When the checkpoint was last updated",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="When the search was completed",
    )
