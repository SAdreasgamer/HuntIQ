"""
HuntIQ — APScheduler & Scraper Automation Service.

Background cron scheduler service for automated job search pipeline execution:
- Scheduled scraping across enabled providers (LinkedIn, Greenhouse, Lever, Ashby, Indeed, Naukri)
- Automated job normalization & deduplication
- Automatic matching pipeline execution against primary candidate resume
- Automated daily analytics snapshot computation
- High-match alert notifications dispatch
- Search checkpoint tracking via SearchCheckpointRepository
"""

from __future__ import annotations

from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession

import app.scrapers.providers  # Import all providers so they self-register in registry
from app.analytics.engine import AnalyticsEngineService
from app.core.logging import get_logger
from app.database import get_session_factory
from app.matcher.composite_matcher import MatchingEngine
from app.notifications.service import NotificationEventType, NotificationService
from app.repositories.search import SearchCheckpointRepository
from app.repositories.user import UserRepository
from app.scrapers.apify_client import ApifyClient
from app.scrapers.normalizer import JobNormalizer
from app.scrapers.registry import get_provider
from app.scrapers.schemas import SearchInput

logger = get_logger(__name__)


class SchedulerService:
    """Service orchestrating background cron jobs and automated scraping pipelines."""

    def __init__(self) -> None:
        """Initialize AsyncIOScheduler."""
        self.scheduler = AsyncIOScheduler()
        self._is_running = False

    def start(self) -> None:
        """Start the background scheduler."""
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logger.info("apscheduler_started_successfully")

    def shutdown(self) -> None:
        """Shutdown the background scheduler."""
        if self._is_running:
            self.scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("apscheduler_shutdown_successfully")

    async def execute_scheduled_pipeline(
        self,
        user_id: str,
        title_keyword: str = "Software Engineer",
        location: str = "Remote",
        provider_names: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute complete automated job search pipeline:
        Scrape -> Normalize -> Match -> Compute Analytics -> Notify.

        Args:
            user_id: User owner ID.
            title_keyword: Job title keyword search.
            location: Preferred location.
            provider_names: Provider keys to execute (defaults to linkedin).

        Returns:
            Dictionary summary of pipeline run.
        """
        session_factory = get_session_factory()
        providers_to_run = provider_names or ["linkedin"]
        total_scraped = 0
        new_saved = 0

        logger.info(
            "scheduled_pipeline_started",
            user_id=user_id,
            title_keyword=title_keyword,
            providers=providers_to_run,
        )

        async with ApifyClient() as apify_client:
            async with session_factory() as session:
                user_repo = UserRepository(session)
                user = await user_repo.get_by_id(user_id)
                if not user:
                    logger.error("scheduled_pipeline_user_not_found", user_id=user_id)
                    return {"status": "error", "message": f"User {user_id} not found"}

                normalizer = JobNormalizer(session)
                search_input = SearchInput(
                    keywords=[title_keyword],
                    locations=[location] if location else [],
                    max_results=25,
                )

                # 1. Scrape and Normalize Jobs
                for p_name in providers_to_run:
                    try:
                        provider = get_provider(p_name, apify_client)
                        result = await provider.search(search_input)
                        total_scraped += result.total_found

                        for raw_job in result.jobs:
                            job_model, is_new = await normalizer.normalize_and_save(raw_job)
                            if is_new:
                                new_saved += 1
                    except Exception as exc:
                        logger.warning(
                            "scheduled_provider_run_failed",
                            provider=p_name,
                            error=str(exc),
                        )

                await session.commit()

                # 2. Run Matching Engine for User
                matching_engine = MatchingEngine()
                matched_results = await matching_engine.batch_match_unscored_jobs(session, user_id, limit=50)
                await session.commit()

                # 3. Compute Daily Analytics Snapshot
                analytics_service = AnalyticsEngineService()
                snapshot = await analytics_service.compute_daily_snapshot(session, user_id)
                await session.commit()

                # 4. Save Search Checkpoint
                checkpoint_repo = SearchCheckpointRepository(session)
                for p_name in providers_to_run:
                    await checkpoint_repo.upsert(
                        provider=p_name,
                        keyword=title_keyword,
                        location=location,
                        last_page=1,
                        total_found=total_scraped,
                    )
                await session.commit()

                # 5. Dispatch Alert Notification if high matches found
                high_matches = [m for m in matched_results if m.composite_score >= 80.0]
                if high_matches:
                    notif_service = NotificationService()
                    top_match = high_matches[0]
                    await notif_service.send_notification(
                        session=session,
                        user_id=user_id,
                        title=f"{len(high_matches)} High AI Matches Found!",
                        message=f"Found {len(high_matches)} new high-matching job opportunities for '{title_keyword}'.",
                        notification_type=NotificationEventType.NEW_HIGH_MATCH_JOB.value,
                        payload={"high_match_count": len(high_matches), "top_job_id": top_match.job_id},
                    )
                    await session.commit()

        summary = {
            "status": "success",
            "user_id": user_id,
            "total_scraped": total_scraped,
            "new_jobs_saved": new_saved,
            "jobs_matched": len(matched_results),
            "high_matches_found": len(high_matches),
        }

        logger.info("scheduled_pipeline_completed_successfully", **summary)
        return summary

    def add_recurring_scrape_job(
        self,
        user_id: str,
        title_keyword: str = "Software Engineer",
        location: str = "Remote",
        cron_expression: str = "0 */6 * * *",
    ) -> str:
        """
        Schedule a recurring cron job for automated scraping pipeline.

        Args:
            user_id: User owner ID.
            title_keyword: Job title search keyword.
            location: Preferred location.
            cron_expression: Cron expression (default: every 6 hours).

        Returns:
            Job ID string in APScheduler.
        """
        job_id = f"scrape_{user_id}_{hash(title_keyword)}"
        parts = cron_expression.split()
        trigger = CronTrigger.from_crontab(cron_expression) if len(parts) == 5 else CronTrigger(hour="*/6")

        self.scheduler.add_job(
            self.execute_scheduled_pipeline,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs={
                "user_id": user_id,
                "title_keyword": title_keyword,
                "location": location,
            },
        )

        logger.info(
            "recurring_scrape_job_scheduled",
            job_id=job_id,
            user_id=user_id,
            cron=cron_expression,
        )
        return job_id
