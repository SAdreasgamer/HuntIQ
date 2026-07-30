"""
HuntIQ — Scheduler & Scraper Automation Service.

Orchestrates the full job search pipeline:
1. Reads user's primary resume to derive targeted search queries
2. Runs the 39-platform AllJobs scraper via Apify for India + Remote roles
3. Normalizes & deduplicates incoming job listings
4. Triggers hybrid rule + vector matching against candidate resume
5. Computes daily time-series analytics snapshots
6. Dispatches notifications for high match results
"""

from __future__ import annotations

from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.analytics.engine import AnalyticsEngineService
from app.config.settings import get_settings
from app.core.logging import get_logger
from app.database import get_session_factory
from app.matcher.composite_matcher import MatchingEngine
from app.notifications.service import NotificationService
from app.repositories.resume import ResumeVersionRepository
from app.repositories.search import SearchCheckpointRepository
from app.repositories.user import UserRepository
import app.scrapers.providers
from app.scrapers.apify_client import ApifyClient
from app.scrapers.normalizer import JobNormalizer
from app.scrapers.registry import get_provider
from app.scrapers.schemas import SearchInput

logger = get_logger(__name__)


class SchedulerService:
    """Service managing scheduled background scraping & matching pipeline."""

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.settings = get_settings()

    async def execute_scheduled_pipeline(
        self,
        user_id: str,
        title_keyword: str = "Software Engineer",
        location: str = "India",
        provider_names: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute full end-to-end job search & matching pipeline.

        Uses the 39-platform AllJobs scraper to fetch real jobs from
        LinkedIn, Indeed, Naukri, Glassdoor, Wellfound, etc.
        Generates resume-derived search queries for maximum relevance.
        """
        session_factory = get_session_factory()
        total_scraped = 0
        new_saved = 0

        logger.info(
            "scheduled_pipeline_started",
            user_id=user_id,
            title_keyword=title_keyword,
            location=location,
        )

        async with ApifyClient() as apify_client:
            async with session_factory() as session:
                user_repo = UserRepository(session)
                user = await user_repo.get_by_id(user_id)
                if not user:
                    logger.error("scheduled_pipeline_user_not_found", user_id=user_id)
                    return {"status": "error", "message": f"User {user_id} not found"}

                # Load user's primary resume to derive targeted search queries
                resume_repo = ResumeVersionRepository(session)
                primary_resume = await resume_repo.get_primary(user_id)

                # Build resume-derived search queries for maximum coverage
                search_queries = self._build_search_queries(primary_resume, title_keyword)

                normalizer = JobNormalizer(session)

                # Run each search query through the 39-platform scraper
                for query_keyword, query_location in search_queries:
                    search_input = SearchInput(
                        keywords=[query_keyword],
                        locations=[query_location],
                        max_results=30,
                    )

                    try:
                        provider = get_provider("all_jobs", apify_client)
                        result = await provider.search(search_input)
                        total_scraped += result.total_found

                        for raw_job in result.jobs:
                            job_model, is_new = await normalizer.normalize_and_save(raw_job)
                            if is_new:
                                new_saved += 1
                    except Exception as exc:
                        logger.warning(
                            "scheduled_search_query_failed",
                            query=query_keyword,
                            location=query_location,
                            error=str(exc),
                        )

                    # Also try LinkedIn directly if available
                    try:
                        linkedin_provider = get_provider("linkedin", apify_client)
                        linkedin_input = SearchInput(
                            keywords=[query_keyword],
                            locations=[query_location],
                            max_results=15,
                        )
                        linkedin_result = await linkedin_provider.search(linkedin_input)
                        total_scraped += linkedin_result.total_found

                        for raw_job in linkedin_result.jobs:
                            job_model, is_new = await normalizer.normalize_and_save(raw_job)
                            if is_new:
                                new_saved += 1
                    except Exception:
                        pass  # LinkedIn is optional, all_jobs already covers it

                await session.commit()

                # Run matching engine against user's resume
                matching_engine = MatchingEngine()
                matched_results = await matching_engine.batch_match_unscored_jobs(session, user_id, limit=100)
                await session.commit()

                # Compute daily analytics snapshot
                analytics_service = AnalyticsEngineService()
                snapshot = await analytics_service.compute_daily_snapshot(session, user_id)
                await session.commit()

                # Save search checkpoint
                checkpoint_repo = SearchCheckpointRepository(session)
                await checkpoint_repo.upsert(
                    provider="all_jobs",
                    keyword=title_keyword,
                    location=location,
                    last_page=1,
                    total_results=total_scraped,
                )
                await session.commit()

                # Notify if high matches found
                high_matches = [m for m in matched_results if m.composite_score >= 70.0]
                if high_matches:
                    notif_service = NotificationService()
                    top_match = high_matches[0]
                    await notif_service.send_notification(
                        session=session,
                        user_id=user_id,
                        title=f"🎯 {len(high_matches)} High-Match Jobs Found!",
                        message=f"Top match: {top_match.composite_score:.1f}% from {total_scraped} scraped across 39 platforms.",
                        channel="in_app",
                        payload={
                            "top_match_id": top_match.job_id,
                            "composite_score": top_match.composite_score,
                        },
                    )
                    await session.commit()

                logger.info(
                    "scheduled_pipeline_completed",
                    user_id=user_id,
                    total_scraped=total_scraped,
                    new_jobs_saved=new_saved,
                    jobs_matched=len(matched_results),
                    high_matches=len(high_matches),
                )

                return {
                    "status": "success",
                    "user_id": user_id,
                    "total_scraped": total_scraped,
                    "new_jobs_saved": new_saved,
                    "jobs_matched": len(matched_results),
                    "high_matches_found": len(high_matches),
                }

    def _build_search_queries(
        self,
        primary_resume: Any | None,
        fallback_keyword: str,
    ) -> list[tuple[str, str]]:
        """
        Build targeted search queries from resume skills and experience.

        Returns list of (keyword, location) tuples.
        """
        queries: list[tuple[str, str]] = []

        if primary_resume and primary_resume.structured_data:
            skills = primary_resume.structured_data.get("skills", [])
            skills_lower = {s.lower() for s in skills}

            # Java/Spring Boot backend roles
            if "java" in skills_lower or "spring boot" in skills_lower:
                queries.append(("Java Spring Boot Backend Developer", "India"))
                queries.append(("Java Backend Engineer", "Remote"))

            # Python backend roles
            if "python" in skills_lower or "fastapi" in skills_lower:
                queries.append(("Python Backend Developer", "India"))
                queries.append(("Python Developer", "Remote"))

            # General SDE/SWE roles
            queries.append(("SDE-1 Software Development Engineer", "India"))
            queries.append(("Associate Software Engineer", "India"))
            queries.append(("Software Engineer", "Remote"))

            # Microservices / distributed
            if "microservices" in skills_lower or "docker" in skills_lower:
                queries.append(("Backend Engineer Microservices", "India"))

            # Cloud / DevOps
            if "aws" in skills_lower or "docker" in skills_lower:
                queries.append(("Backend Engineer AWS Docker", "Remote"))

        # Fallback queries if no resume or few skills
        if len(queries) < 3:
            queries.extend([
                (fallback_keyword, "India"),
                (f"{fallback_keyword} Backend", "India"),
                (f"{fallback_keyword}", "Remote"),
            ])

        # Deduplicate while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            if q not in seen:
                seen.add(q)
                unique_queries.append(q)

        return unique_queries
