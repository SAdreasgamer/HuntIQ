"""
Recruiter ORM model.

Stores recruiter/hiring manager contacts linked to companies.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, NotesMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Recruiter(Base, UUIDPrimaryKeyMixin, TimestampMixin, NotesMixin):
    """Recruiter or hiring manager contact."""

    __tablename__ = "recruiters"

    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to company",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Recruiter full name",
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        doc="Recruiter email address",
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        doc="Recruiter phone number",
    )
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        doc="Recruiter job title",
    )
    linkedin_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        default=None,
        doc="Recruiter LinkedIn profile URL",
    )
    department: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        doc="Department the recruiter handles",
    )
    last_contacted_at: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        doc="When the recruiter was last contacted",
    )
    response_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        doc="Response status: pending, responded, no_response",
    )

    # Relationship
    company: Mapped[Company] = relationship("Company", back_populates="recruiters")


# Forward reference
from app.models.company import Company  # noqa: E402
