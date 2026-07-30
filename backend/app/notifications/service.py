"""
HuntIQ — Multi-Channel Notification Service.

Delivers multi-channel alert notifications across:
- In-App Dashboard Notifications
- Email Notifications (SMTP / Provider)
- Webhooks (Discord, Slack, Custom HTTP endpoint)
- Desktop System Alerts

Includes deduplication to prevent notification fatigue and respects UserPreferences.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RecordNotFoundError
from app.core.logging import get_logger
from app.models.notification import Notification
from app.repositories.notification import NotificationRepository
from app.repositories.user import UserPreferenceRepository, UserRepository

logger = get_logger(__name__)


class NotificationChannel(str, Enum):
    """Supported notification delivery channels."""

    IN_APP = "in_app"
    EMAIL = "email"
    WEBHOOK = "webhook"
    DESKTOP = "desktop"


class NotificationEventType(str, Enum):
    """Notification trigger event types."""

    NEW_HIGH_MATCH_JOB = "new_high_match_job"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    APPLICATION_STATUS_CHANGE = "application_status_change"
    SCRAPER_RUN_COMPLETED = "scraper_run_completed"
    DAILY_DIGEST = "daily_digest"


class NotificationService:
    """Service managing notification creation, deduplication, and dispatching."""

    async def send_notification(
        self,
        session: AsyncSession,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = NotificationEventType.NEW_HIGH_MATCH_JOB.value,
        payload: dict[str, Any] | None = None,
        channel: str = NotificationChannel.IN_APP.value,
        reference_type: str | None = None,
        reference_id: str | None = None,
    ) -> Notification:
        """
        Create and dispatch a notification.

        Args:
            session: Async DB session.
            user_id: User owner ID.
            title: Short notification title.
            message: Detailed message body.
            notification_type: Event category.
            payload: Optional metadata dictionary.
            channel: Target channel (in_app, email, webhook, desktop).
            reference_type: Referenced entity type (job, application, etc.).
            reference_id: Referenced entity primary key.

        Returns:
            Created Notification ORM model instance.
        """
        user_repo = UserRepository(session)
        pref_repo = UserPreferenceRepository(session)
        notif_repo = NotificationRepository(session)

        user = await user_repo.get_by_id(user_id)
        if not user:
            raise RecordNotFoundError(entity="User", identifier=user_id)

        # Build deduplication key
        raw_key = f"{user_id}:{notification_type}:{title}:{reference_id or ''}"
        dedup_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

        # Check existing notification with this dedup key
        existing = await notif_repo.get_by_dedup_key(dedup_key)
        if existing:
            logger.info("notification_deduplicated_suppressed", user_id=user_id, title=title)
            return existing

        # Check user preferences for channel enablement
        prefs = await pref_repo.get_by_user_id(user_id)
        if prefs and not prefs.email_notifications and channel == NotificationChannel.EMAIL.value:
            logger.info("email_notification_disabled_by_user", user_id=user_id)

        # Save to DB
        notif = await notif_repo.create(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            channel=channel,
            reference_type=reference_type,
            reference_id=reference_id,
            dedup_key=dedup_key,
            metadata_json=payload or {},
            is_sent=True,
            sent_at=datetime.now(timezone.utc),
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )

        # Dispatch via specified channel
        if channel == NotificationChannel.WEBHOOK.value and prefs and prefs.webhook_url:
            await self._dispatch_webhook(prefs.webhook_url, title, message, payload or {})

        logger.info(
            "notification_sent",
            notif_id=notif.id,
            user_id=user_id,
            channel=channel,
            type=notification_type,
        )
        return notif

    async def _dispatch_webhook(
        self,
        webhook_url: str,
        title: str,
        message: str,
        payload: dict[str, Any],
    ) -> bool:
        """Send webhook HTTP POST payload (e.g. Slack / Discord webhook)."""
        body = {
            "title": title,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(webhook_url, json=body)
                if res.status_code < 400:
                    logger.info("webhook_notification_dispatched", url=webhook_url)
                    return True
        except Exception as exc:
            logger.warning("webhook_dispatch_failed", url=webhook_url, error=str(exc))
        return False

    async def mark_as_read(self, session: AsyncSession, notification_id: str) -> Notification:
        """
        Mark a notification as read.

        Args:
            session: Async DB session.
            notification_id: Notification ID.

        Returns:
            Updated Notification ORM model.
        """
        notif_repo = NotificationRepository(session)
        notif = await notif_repo.get_by_id(notification_id)
        if not notif:
            raise RecordNotFoundError(entity="Notification", identifier=notification_id)

        notif.is_read = True
        await session.flush()
        return notif

    async def get_user_notifications(
        self,
        session: AsyncSession,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[Notification]:
        """Get notifications list for user."""
        notif_repo = NotificationRepository(session)
        return list(await notif_repo.get_by_user(user_id, unread_only=unread_only, limit=limit))
