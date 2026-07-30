"""
HuntIQ — Lever Job Provider.

Scrapes Lever ATS job boards via Apify's Lever scraper actor.
Handles Lever-specific data schemas and maps them to RawJobData.

Actor: apify/lever-scraper
Docs: https://apify.com/apify/lever-scraper
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.scrapers.base_provider import JobProvider
from app.scrapers.registry import register_provider
from app.scrapers.schemas import RawJobData, SearchInput

logger = get_logger(__name__)


@register_provider
class LeverProvider(JobProvider):
    """Lever ATS job scraper using Apify."""

    provider_name = "lever"
    actor_id = "apify/lever-scraper"

    default_memory_mbytes = 256
    default_timeout_secs = 300

    def build_actor_input(self, search_input: SearchInput) -> dict[str, Any]:
        """
        Build Lever-specific Apify actor input.

        Maps generic search parameters to the lever actor's input schema.
        """
        keywords = search_input.keywords or ["backend"]
        locations = search_input.locations or []

        return {
            "searchKeywords": keywords,
            "locations": locations,
            "maxItems": search_input.max_results,
            "proxy": {
                "useApifyProxy": True,
            },
        }

    def parse_result(self, raw_item: dict[str, Any]) -> RawJobData | None:
        """
        Parse a single Lever job listing into RawJobData.

        Lever items typically include:
        id, text/title, company, categories (location, team, commitment),
        hostedUrl, applyUrl, description, createdAt, etc.
        """
        title = (raw_item.get("text") or raw_item.get("title") or "").strip()
        company = (
            raw_item.get("company")
            or raw_item.get("companyName")
            or raw_item.get("company_name")
            or ""
        ).strip()

        if not title:
            return None

        if not company:
            company = "Lever Company"

        # Lever stores location under categories -> location
        categories = raw_item.get("categories") or {}
        location_str = ""
        employment_type = "full-time"

        if isinstance(categories, dict):
            location_str = str(categories.get("location") or "").strip()
            commitment = categories.get("commitment") or ""
            if commitment:
                employment_type = str(commitment).lower()
        elif raw_item.get("location"):
            location_str = str(raw_item.get("location")).strip()

        is_remote = self._detect_remote(location_str, raw_item)
        description = raw_item.get("description") or raw_item.get("content") or ""

        # Extract skills from description
        skills = self.extract_skills_from_text(description)

        # Parse date
        posted_at = self._parse_date(raw_item.get("createdAt") or raw_item.get("created_at") or raw_item.get("postedAt"))

        posting_url = raw_item.get("hostedUrl") or raw_item.get("url") or raw_item.get("link")
        apply_url = raw_item.get("applyUrl") or posting_url
        external_id = str(raw_item.get("id") or raw_item.get("job_id") or "")

        return RawJobData(
            title=title,
            company_name=company,
            source_type=self.provider_name,
            location=location_str if location_str else None,
            is_remote=is_remote,
            country=self._extract_country(location_str),
            description=description if description else None,
            employment_type=employment_type,
            posting_url=posting_url,
            apply_url=apply_url,
            external_id=external_id if external_id else None,
            skills=skills,
            tech_stack=skills,
            posted_at=posted_at,
            raw_data=raw_item,
        )

    def _detect_remote(self, location: str, raw: dict[str, Any]) -> bool:
        """Detect if job is remote."""
        if not location:
            return False
        loc_lower = location.lower()
        if any(term in loc_lower for term in ["remote", "wfh", "anywhere", "distributed", "flexible"]):
            return True
        workplace = str(raw.get("workplaceType") or raw.get("workplace") or "").lower()
        return "remote" in workplace

    def _extract_country(self, location: str) -> str | None:
        """Extract country from location string."""
        if not location:
            return None
        parts = [p.strip() for p in location.split(",")]
        return parts[-1] if parts else None

    def _parse_date(self, date_val: Any) -> datetime | None:
        """Parse timestamp or ISO string into datetime object."""
        if not date_val:
            return None
        if isinstance(date_val, datetime):
            return date_val
        # Epoch timestamp in milliseconds
        if isinstance(date_val, (int, float)):
            try:
                return datetime.fromtimestamp(date_val / 1000.0, tz=timezone.utc)
            except (OSError, ValueError):
                return None
        try:
            return datetime.fromisoformat(str(date_val).replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
