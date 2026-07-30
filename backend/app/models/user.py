"""
User and UserPreference ORM models.

Handles authentication identity and per-user configuration
for search preferences, blacklists, and notification settings.
"""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User account for authentication and identity."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="User email address (login identifier)",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Bcrypt-hashed password",
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="User display name",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the account is active",
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the user has admin privileges",
    )

    # Relationships
    preferences: Mapped[UserPreference | None] = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    resume_versions: Mapped[list[ResumeVersion]] = relationship(
        "ResumeVersion",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    applications: Mapped[list[Application]] = relationship(
        "Application",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    bookmarks: Mapped[list[Bookmark]] = relationship(
        "Bookmark",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    notifications: Mapped[list[Notification]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )


class UserPreference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Per-user search and notification preferences."""

    __tablename__ = "user_preferences"

    user_id: Mapped[str] = mapped_column(
        String(36),
        __import__("sqlalchemy").ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        doc="FK to user",
    )

    # Search preferences (stored as JSON lists for flexibility)
    preferred_roles: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="List of preferred job roles/titles",
    )
    preferred_locations: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="List of preferred locations",
    )
    preferred_companies: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="List of preferred company names",
    )
    blacklisted_companies: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="List of companies to exclude",
    )
    preferred_technologies: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="List of preferred technologies/languages",
    )
    blacklisted_keywords: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="List of keywords to filter out",
    )

    # Numeric preferences
    minimum_salary: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        doc="Minimum acceptable salary",
    )
    maximum_experience: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        doc="Maximum years of experience to target",
    )

    # Notification preferences
    notification_threshold: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
        doc="Minimum match score to trigger notification (0-100)",
    )
    search_frequency_hours: Mapped[int] = mapped_column(
        Integer,
        default=6,
        nullable=False,
        doc="Hours between automatic job searches",
    )

    # Active resume for matching
    active_resume_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        default=None,
        doc="ID of the resume version to use for matching",
    )

    # Relationship
    user: Mapped[User] = relationship("User", back_populates="preferences")


# Forward references for relationships defined in other modules
from app.models.application import Application  # noqa: E402
from app.models.bookmark import Bookmark  # noqa: E402
from app.models.notification import Notification  # noqa: E402
from app.models.resume import ResumeVersion  # noqa: E402
