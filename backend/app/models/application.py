"""
Application and ApplicationStageHistory ORM models.

Tracks the full lifecycle of job applications from
'Not Applied' through to 'Offer' or 'Rejected',
with a complete stage transition history.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, NotesMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Application(Base, UUIDPrimaryKeyMixin, TimestampMixin, NotesMixin):
    """Tracks a job application through its lifecycle."""

    __tablename__ = "applications"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to user",
    )
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to job",
    )

    # Application details
    current_stage: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="not_applied",
        index=True,
        doc="Current application stage",
    )
    application_url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        default=None,
        doc="URL where the application was submitted",
    )
    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="When the application was submitted",
    )
    resume_version_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        default=None,
        doc="Resume version used for this application",
    )
    cover_letter: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="Cover letter used for this application",
    )

    # Recruiter info
    recruiter_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        doc="Recruiter or hiring manager name",
    )
    recruiter_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        doc="Recruiter email address",
    )

    # Interview tracking
    next_interview_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Next scheduled interview date/time",
    )

    # Outcome
    offer_amount: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
        doc="Offer amount if received",
    )
    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="Reason for rejection if applicable",
    )

    # Source tracking
    source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        doc="How the application was sourced (direct, referral, etc.)",
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="applications")
    job: Mapped[Job] = relationship("Job", back_populates="applications")
    stage_history: Mapped[list[ApplicationStageHistory]] = relationship(
        "ApplicationStageHistory",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationStageHistory.transitioned_at",
        lazy="selectin",
    )


class ApplicationStageHistory(Base, UUIDPrimaryKeyMixin):
    """Records each stage transition for an application."""

    __tablename__ = "application_stage_histories"

    application_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to application",
    )
    from_stage: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        doc="Previous stage (null for initial stage)",
    )
    to_stage: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="New stage",
    )
    transitioned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="When the stage transition occurred",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="Notes about this transition",
    )

    # Relationship
    application: Mapped[Application] = relationship(
        "Application",
        back_populates="stage_history",
    )


# Forward references
from app.models.job import Job  # noqa: E402
from app.models.user import User  # noqa: E402
