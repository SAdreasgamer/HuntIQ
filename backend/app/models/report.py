"""
Report ORM model.

Stores metadata about generated Excel reports.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin


class Report(Base, UUIDPrimaryKeyMixin):
    """Generated report metadata."""

    __tablename__ = "reports"

    report_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Report type: daily, weekly, monthly, custom",
    )
    file_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        doc="Path to the generated report file",
    )
    file_size_bytes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        doc="File size in bytes",
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Human-readable report title",
    )
    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        default=None,
        doc="Report description",
    )

    # Content metadata
    total_jobs: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total number of jobs in the report",
    )
    total_matches: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of matches included",
    )
    worksheets: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="List of worksheet names and row counts",
    )
    parameters: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Parameters/filters used to generate the report",
    )

    # Timestamps
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When the report was generated",
    )
    period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Start of the reporting period",
    )
    period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="End of the reporting period",
    )
