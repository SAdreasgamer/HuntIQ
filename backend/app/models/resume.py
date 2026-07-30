"""
ResumeVersion, ResumeSkill, and ResumeEmbedding ORM models.

Supports multiple resume variants per user. The PDF is parsed
ONCE and stored as structured JSON. All downstream operations
use the JSON, never re-parse the PDF.
"""

from __future__ import annotations

from sqlalchemy import (
    Float,
    Boolean,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ResumeVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A specific version/variant of a user's resume.

    Supports multiple resume types (e.g., Backend Resume,
    Java Resume, Platform Resume) per user.
    """

    __tablename__ = "resume_versions"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to user",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Resume variant name (e.g., 'Backend Resume')",
    )
    file_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        doc="Path to the original PDF file on disk",
    )
    file_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="SHA-256 hash of the PDF file for change detection",
    )

    # Parsed structured data (the core output of resume parsing)
    structured_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        doc="Complete structured resume as JSON (skills, experience, education, etc.)",
    )

    # Extracted summary fields for quick access
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="Professional summary / objective text",
    )
    total_experience_years: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        default=None,
        doc="Total years of professional experience",
    )
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        doc="Full name extracted from resume",
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        doc="Email extracted from resume",
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        doc="Phone number extracted from resume",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether this resume version is active for matching",
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this is the primary resume version",
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="resume_versions")
    skills: Mapped[list[ResumeSkill]] = relationship(
        "ResumeSkill",
        back_populates="resume_version",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    embedding: Mapped[ResumeEmbedding | None] = relationship(
        "ResumeEmbedding",
        back_populates="resume_version",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="noload",
    )


class ResumeSkill(Base, UUIDPrimaryKeyMixin):
    """Skill extracted from a resume version."""

    __tablename__ = "resume_skills"
    __table_args__ = (
        UniqueConstraint(
            "resume_version_id",
            "skill_name",
            name="uq_resume_skill",
        ),
    )

    resume_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("resume_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to resume version",
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
    proficiency_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        doc="Self-reported proficiency: beginner, intermediate, advanced, expert",
    )
    years_of_experience: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        default=None,
        doc="Years of experience with this skill",
    )

    # Relationship
    resume_version: Mapped[ResumeVersion] = relationship(
        "ResumeVersion",
        back_populates="skills",
    )


class ResumeEmbedding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Vector embedding for a resume version."""

    __tablename__ = "resume_embeddings"

    resume_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("resume_versions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        doc="FK to resume version",
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
    resume_version: Mapped[ResumeVersion] = relationship(
        "ResumeVersion",
        back_populates="embedding",
    )


# Forward reference
from app.models.user import User  # noqa: E402
