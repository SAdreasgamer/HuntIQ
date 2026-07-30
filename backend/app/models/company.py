"""
Company ORM model.

Stores company intelligence data including hiring patterns,
tech stack, and user preference flags.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Company(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Company intelligence and metadata."""

    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        doc="Company name",
    )
    normalized_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
        doc="Lowercased, stripped company name for deduplication",
    )
    website: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        default=None,
        doc="Company website URL",
    )
    industry: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        doc="Company industry/sector",
    )
    company_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        doc="Company type: startup, mnc, mid_size, etc.",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="Company description/about",
    )
    logo_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        default=None,
        doc="Company logo URL",
    )
    headquarters: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        doc="Company headquarters location",
    )
    employee_count: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        doc="Employee count range (e.g., '100-500')",
    )

    # Intelligence fields
    known_tech_stack: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Known technologies used by the company",
    )
    remote_friendly: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        default=None,
        doc="Whether the company supports remote work",
    )
    average_salary: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        doc="Average salary offered (in local currency)",
    )
    hiring_frequency: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        doc="Hiring frequency: high, medium, low",
    )
    average_match_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        default=None,
        doc="Average match score across all jobs from this company",
    )
    total_jobs_found: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total number of jobs found from this company",
    )
    total_applications: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total applications submitted to this company",
    )

    # User preference
    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether the user has marked this company as favorite",
    )
    is_blacklisted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether the user has blacklisted this company",
    )

    # Relationships
    jobs: Mapped[list[Job]] = relationship(
        "Job",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    recruiters: Mapped[list[Recruiter]] = relationship(
        "Recruiter",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="noload",
    )


# Forward references
from app.models.job import Job  # noqa: E402
from app.models.recruiter import Recruiter  # noqa: E402
