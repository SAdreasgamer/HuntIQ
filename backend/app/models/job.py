"""
Job, JobSkill, JobSource, and JobEmbedding ORM models.

Core models for storing normalized job listings, their extracted
skills, source provider tracking, and vector embeddings.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Job(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Normalized job listing."""

    __tablename__ = "jobs"

    # Core fields
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        doc="Job title/role",
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to company",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="Full job description text",
    )
    requirements: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="Job requirements text",
    )
    responsibilities: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="Job responsibilities text",
    )

    # Location
    location: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
        index=True,
        doc="Job location",
    )
    is_remote: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether the job is remote",
    )
    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
        index=True,
        doc="Country of the job",
    )

    # Compensation
    salary_min: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        doc="Minimum salary",
    )
    salary_max: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        doc="Maximum salary",
    )
    salary_currency: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        default=None,
        doc="Salary currency code (USD, INR, etc.)",
    )
    salary_period: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
        doc="Salary period: yearly, monthly, hourly",
    )

    # Experience
    experience_min: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        doc="Minimum years of experience required",
    )
    experience_max: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        doc="Maximum years of experience required",
    )
    seniority_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        doc="Seniority level: entry, mid, senior, lead",
    )

    # Employment details
    employment_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        doc="Type: full-time, part-time, contract, internship",
    )

    # URLs and identifiers
    posting_url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        default=None,
        doc="Original job posting URL",
    )
    apply_url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        default=None,
        doc="Direct application URL",
    )
    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        index=True,
        doc="External job ID from the source platform",
    )

    # Structured data (JSON)
    tech_stack: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Technologies/tech stack extracted from the job",
    )
    structured_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Full structured job data as JSON",
    )

    # Content hash for deduplication
    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        default=None,
        index=True,
        doc="SHA-256 hash of normalized content for dedup",
    )

    # Posting dates
    posted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
        doc="When the job was originally posted",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="When the job posting expires",
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="When the job was last seen in a search",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether the job posting is still active",
    )
    is_duplicate: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this is a detected duplicate",
    )
    duplicate_of_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        doc="FK to the canonical job if this is a duplicate",
    )

    # Matching
    match_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        default=None,
        index=True,
        doc="Final composite match score (0-100)",
    )
    rule_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        default=None,
        doc="Rule-based match score (0-100)",
    )
    embedding_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        default=None,
        doc="Embedding similarity score (0-100)",
    )
    llm_score_adjustment: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        default=None,
        doc="LLM-provided score adjustment (-10 to +10)",
    )
    match_explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="LLM-generated match explanation",
    )
    missing_skills: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Skills missing from resume for this job",
    )
    apply_recommendation: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
        doc="LLM recommendation: yes, no, maybe",
    )
    matched_resume_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        default=None,
        doc="Resume version ID used for matching",
    )

    # Relationships
    company: Mapped[Company] = relationship("Company", back_populates="jobs")
    skills: Mapped[list[JobSkill]] = relationship(
        "JobSkill",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    sources: Mapped[list[JobSource]] = relationship(
        "JobSource",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    embedding: Mapped[JobEmbedding | None] = relationship(
        "JobEmbedding",
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="noload",
    )
    applications: Mapped[list[Application]] = relationship(
        "Application",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    bookmarks: Mapped[list[Bookmark]] = relationship(
        "Bookmark",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    duplicate_original: Mapped[Job | None] = relationship(
        "Job",
        remote_side="Job.id",
        foreign_keys=[duplicate_of_id],
        lazy="noload",
    )


class JobSkill(Base, UUIDPrimaryKeyMixin):
    """Skill extracted from a job listing."""

    __tablename__ = "job_skills"
    __table_args__ = (
        UniqueConstraint("job_id", "skill_name", name="uq_job_skill"),
    )

    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to job",
    )
    skill_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Normalized skill name",
    )
    skill_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
        doc="Skill category: language, framework, tool, etc.",
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the skill is required vs. nice-to-have",
    )

    # Relationship
    job: Mapped[Job] = relationship("Job", back_populates="skills")


class JobSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks which provider found each job."""

    __tablename__ = "job_sources"
    __table_args__ = (
        UniqueConstraint("job_id", "source_type", name="uq_job_source"),
    )

    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to job",
    )
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Provider type: linkedin, greenhouse, etc.",
    )
    source_url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        default=None,
        doc="URL where this job was found",
    )
    source_job_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        doc="Job ID on the source platform",
    )
    raw_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Original raw data from the provider",
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="When this job was first seen from this source",
    )

    # Relationship
    job: Mapped[Job] = relationship("Job", back_populates="sources")


class JobEmbedding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Vector embedding for a job listing."""

    __tablename__ = "job_embeddings"

    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        doc="FK to job",
    )
    embedding: Mapped[dict | list] = mapped_column(
        JSON,
        nullable=False,
        doc="Embedding vector as JSON array of floats",
    )
    model_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Name of the embedding model used",
    )
    dimensions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Number of embedding dimensions",
    )
    source_text_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Hash of the source text used for embedding",
    )

    # Relationship
    job: Mapped[Job] = relationship("Job", back_populates="embedding")


# Forward references
from app.models.application import Application  # noqa: E402
from app.models.bookmark import Bookmark  # noqa: E402
from app.models.company import Company  # noqa: E402
