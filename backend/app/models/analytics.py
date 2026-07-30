"""
AnalyticsSnapshot ORM model.

Stores periodic aggregated metrics for trend analysis.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin


class AnalyticsSnapshot(Base, UUIDPrimaryKeyMixin):
    """Periodic analytics snapshot for trend tracking."""

    __tablename__ = "analytics_snapshots"

    snapshot_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Snapshot period: daily, weekly, monthly",
    )
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Date of the snapshot",
    )

    # Job counts
    total_jobs: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total jobs in the system",
    )
    new_jobs: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="New jobs found in this period",
    )
    active_jobs: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Active (non-closed) jobs",
    )
    remote_jobs: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Remote job count",
    )

    # Match counts
    total_matches: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total jobs with match scores",
    )
    high_matches: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Jobs with match score > threshold",
    )
    average_match_score: Mapped[float | None] = mapped_column(
        __import__("sqlalchemy").Float,
        nullable=True,
        default=None,
        doc="Average match score across all jobs",
    )

    # Application counts
    total_applications: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total applications submitted",
    )
    interviews: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Interview invitations received",
    )
    offers: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Offers received",
    )
    rejections: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Rejections received",
    )

    # Detailed breakdowns (stored as JSON for flexibility)
    top_companies: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Top hiring companies with job counts",
    )
    top_skills: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Top in-demand skills with counts",
    )
    skill_gaps: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Skills frequently missing from resume",
    )
    salary_distribution: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Salary distribution stats (min, max, avg, median)",
    )
    source_performance: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Jobs found per source provider",
    )
    location_distribution: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Job distribution by location",
    )
    hiring_trends: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Hiring trend data points",
    )

    # Metadata
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="When this snapshot was generated",
    )
