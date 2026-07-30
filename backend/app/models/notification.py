"""
Notification ORM model.

Tracks notification history and delivery status.
Deduplication prevents sending the same notification twice.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDPrimaryKeyMixin


class Notification(Base, UUIDPrimaryKeyMixin):
    """Notification record with delivery tracking."""

    __tablename__ = "notifications"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to user",
    )

    # What triggered this notification
    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Type: high_match, favorite_company, new_job, etc.",
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Notification title",
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Notification body message",
    )

    # Reference to the entity that triggered it
    reference_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        doc="Type of referenced entity: job, application, report",
    )
    reference_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        default=None,
        doc="ID of the referenced entity",
    )

    # Delivery
    channel: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Delivery channel: email, desktop, webhook",
    )
    is_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether the notification was successfully sent",
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="When the notification was sent",
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the user has read the notification",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="Error message if delivery failed",
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of delivery retries",
    )

    # Deduplication
    dedup_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="Deduplication key to prevent duplicate notifications",
    )

    # Metadata
    metadata_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Additional notification metadata",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When the notification was created",
    )

    # Relationship
    user: Mapped[User] = relationship("User", back_populates="notifications")


# Forward reference
from app.models.user import User  # noqa: E402
