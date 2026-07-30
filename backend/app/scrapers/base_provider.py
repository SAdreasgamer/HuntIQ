"""
HuntIQ — Abstract Job Provider Base Class.

Every job source provider (LinkedIn, Greenhouse, Lever, etc.)
must inherit from JobProvider and implement its abstract methods.

The ABC enforces a consistent interface:
1. `search()` — Execute a search and return RawJobData items
2. `build_actor_input()` — Build Apify actor input from search params
3. `parse_results()` — Convert raw Apify results into RawJobData
4. `provider_name` — Unique identifier for this provider

Usage:
    @register_provider
    class LinkedInProvider(JobProvider):
        provider_name = "linkedin"
        actor_id = "apify/linkedin-jobs-scraper"
        ...
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from app.core.exceptions import ProviderError
from app.core.logging import get_logger
from app.scrapers.apify_client import ApifyClient
from app.scrapers.schemas import ProviderResult, RawJobData, SearchInput

logger = get_logger(__name__)


class JobProvider(ABC):
    """
    Abstract base class for all job source providers.

    Each provider knows how to:
    1. Build Apify actor input for its platform
    2. Parse platform-specific results into RawJobData
    3. Handle platform-specific quirks and edge cases

    The search() method orchestrates the full flow:
    build input → run actor → parse results → return ProviderResult
    """

    # Subclasses MUST set these
    provider_name: str = ""
    actor_id: str = ""

    # Optional overrides
    default_memory_mbytes: int = 256
    default_timeout_secs: int = 300

    def __init__(self, apify_client: ApifyClient) -> None:
        """
        Initialize the provider with an Apify client.

        Args:
            apify_client: An initialized ApifyClient instance.
        """
        self.apify = apify_client

    async def search(self, search_input: SearchInput) -> ProviderResult:
        """
        Execute a job search on this provider's platform.

        This is the main entry point. It:
        1. Builds the Apify actor input
        2. Runs the actor
        3. Parses the raw results
        4. Returns a structured ProviderResult

        Args:
            search_input: Search parameters (keywords, locations, etc.).

        Returns:
            ProviderResult with scraped jobs and metadata.
        """
        start_time = time.monotonic()
        errors: list[str] = []

        logger.info(
            "provider_search_starting",
            provider=self.provider_name,
            keywords=search_input.keywords,
            locations=search_input.locations,
        )

        try:
            # Build platform-specific actor input
            actor_input = self.build_actor_input(search_input)

            # Run the Apify actor
            run_data = await self.apify.run_actor(
                actor_id=self.actor_id,
                input_data=actor_input,
                memory_mbytes=self.default_memory_mbytes,
                timeout_secs=self.default_timeout_secs,
                wait_for_finish=True,
            )

            # Retrieve raw results from the dataset
            dataset_id = run_data.get("defaultDatasetId", "")
            if not dataset_id:
                errors.append("No dataset ID returned from actor run")
                return ProviderResult(
                    provider_name=self.provider_name,
                    errors=errors,
                    duration_seconds=time.monotonic() - start_time,
                )

            raw_items = await self.apify.get_dataset_items(dataset_id)

            # Parse raw items into standardized RawJobData
            jobs: list[RawJobData] = []
            for item in raw_items:
                try:
                    parsed = self.parse_result(item)
                    if parsed is not None:
                        jobs.append(parsed)
                except Exception as exc:
                    errors.append(f"Failed to parse item: {exc}")
                    logger.warning(
                        "provider_parse_error",
                        provider=self.provider_name,
                        error=str(exc),
                    )

            # Apply post-processing filters
            jobs = self.filter_results(jobs, search_input)

            elapsed = time.monotonic() - start_time
            logger.info(
                "provider_search_completed",
                provider=self.provider_name,
                total_raw=len(raw_items),
                total_parsed=len(jobs),
                errors=len(errors),
                duration_seconds=round(elapsed, 2),
            )

            return ProviderResult(
                provider_name=self.provider_name,
                jobs=jobs,
                total_found=len(raw_items),
                errors=errors,
                duration_seconds=elapsed,
            )

        except ProviderError:
            raise
        except Exception as exc:
            elapsed = time.monotonic() - start_time
            error_msg = f"Unexpected error in {self.provider_name}: {exc}"
            logger.error(
                "provider_search_failed",
                provider=self.provider_name,
                error=str(exc),
                duration_seconds=round(elapsed, 2),
            )
            raise ProviderError(
                provider=self.provider_name,
                message=error_msg,
            ) from exc

    @abstractmethod
    def build_actor_input(self, search_input: SearchInput) -> dict[str, Any]:
        """
        Build the Apify actor input from search parameters.

        Each provider translates generic search params into
        platform-specific actor configuration.

        Args:
            search_input: Generic search parameters.

        Returns:
            Dict of actor input configuration.
        """

    @abstractmethod
    def parse_result(self, raw_item: dict[str, Any]) -> RawJobData | None:
        """
        Parse a single raw result item into a RawJobData instance.

        Returns None if the item should be skipped (invalid/incomplete).

        Args:
            raw_item: Raw dict from Apify dataset.

        Returns:
            RawJobData instance, or None to skip.
        """

    def filter_results(
        self,
        jobs: list[RawJobData],
        search_input: SearchInput,
    ) -> list[RawJobData]:
        """
        Apply post-processing filters to parsed results.

        Default implementation filters out jobs matching excluded keywords.
        Providers can override for platform-specific filtering.

        Args:
            jobs: List of parsed jobs.
            search_input: Original search parameters.

        Returns:
            Filtered list of jobs.
        """
        if not search_input.excluded_keywords:
            return jobs

        excluded_lower = {kw.lower() for kw in search_input.excluded_keywords}

        filtered: list[RawJobData] = []
        for job in jobs:
            title_lower = job.title.lower()
            # Skip if title contains any excluded keyword
            if any(kw in title_lower for kw in excluded_lower):
                continue
            filtered.append(job)

        excluded_count = len(jobs) - len(filtered)
        if excluded_count > 0:
            logger.info(
                "provider_filter_excluded",
                provider=self.provider_name,
                excluded_count=excluded_count,
            )

        return filtered

    def extract_skills_from_text(self, text: str) -> list[str]:
        """
        Extract technology/skill names from job description text.

        This is a basic keyword-based extraction. LLM-based extraction
        happens later in the pipeline for more accuracy.

        Args:
            text: Job description or requirements text.

        Returns:
            List of extracted skill/technology names.
        """
        if not text:
            return []

        # Common tech keywords to look for
        tech_keywords = {
            "python", "java", "javascript", "typescript", "go", "golang", "rust",
            "c++", "c#", "ruby", "php", "swift", "kotlin", "scala", "r",
            "react", "angular", "vue", "next.js", "node.js", "express",
            "django", "flask", "fastapi", "spring", "spring boot",
            "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
            "terraform", "ansible", "jenkins", "github actions", "ci/cd",
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "kafka", "rabbitmq", "graphql", "rest", "grpc",
            "microservices", "distributed systems", "machine learning", "deep learning",
            "pytorch", "tensorflow", "pandas", "numpy", "spark",
            "sql", "nosql", "linux", "git", "agile", "scrum",
        }

        text_lower = text.lower()
        found = []
        for keyword in tech_keywords:
            if keyword in text_lower:
                found.append(keyword)

        return sorted(set(found))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(provider={self.provider_name}, actor={self.actor_id})>"
