"""
Bookmark and BookmarkTag ORM models.

Allows saving jobs with priority, notes, tags, and reminders.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Bookmark(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A bookmarked/saved job listing."""

    __tablename__ = "bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_user_bookmark"),
    )

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
    priority: Mapped[str] = mapped_column(
        String(20),
        default="medium",
        nullable=False,
        index=True,
        doc="Priority: low, medium, high, urgent",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="User notes about this bookmark",
    )
    reminder_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Reminder date/time for this bookmark",
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="bookmarks")
    job: Mapped[Job] = relationship("Job", back_populates="bookmarks")
    tags: Mapped[list[BookmarkTag]] = relationship(
        "BookmarkTag",
        back_populates="bookmark",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class BookmarkTag(Base, UUIDPrimaryKeyMixin):
    """Tag associated with a bookmark for organization."""

    __tablename__ = "bookmark_tags"
    __table_args__ = (
        UniqueConstraint("bookmark_id", "tag_name", name="uq_bookmark_tag"),
    )

    bookmark_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("bookmarks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to bookmark",
    )
    tag_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Tag name",
    )

    # Relationship
    bookmark: Mapped[Bookmark] = relationship("Bookmark", back_populates="tags")


# Forward references
from app.models.job import Job  # noqa: E402
from app.models.user import User  # noqa: E402
