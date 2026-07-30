"""
HuntIQ — Greenhouse Job Provider.

Scrapes Greenhouse ATS job boards via Apify's Greenhouse scraper actor.
Handles Greenhouse-specific data schemas and maps them to RawJobData.

Actor: apify/greenhouse-scraper (or custom greenhouse API integration)
Docs: https://apify.com/apify/greenhouse-scraper
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
class GreenhouseProvider(JobProvider):
    """Greenhouse ATS job scraper using Apify."""

    provider_name = "greenhouse"
    actor_id = "apify/greenhouse-scraper"

    default_memory_mbytes = 256
    default_timeout_secs = 300

    def build_actor_input(self, search_input: SearchInput) -> dict[str, Any]:
        """
        Build Greenhouse-specific Apify actor input.

        Maps generic search parameters to the greenhouse actor's schema.
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
        Parse a single Greenhouse job listing into RawJobData.

        Greenhouse items typically include:
        id, title, company_name, location, absolute_url,
        content/description, updated_at, departments, offices, etc.
        """
        title = (raw_item.get("title") or raw_item.get("job_title") or "").strip()
        company = (
            raw_item.get("company_name")
            or raw_item.get("companyName")
            or raw_item.get("company")
            or ""
        ).strip()

        if not title:
            return None

        # Fallback company name if omitted in board output
        if not company:
            company = "Greenhouse Company"

        location = raw_item.get("location", {}).get("name") if isinstance(raw_item.get("location"), dict) else raw_item.get("location")
        location_str = str(location).strip() if location else ""

        is_remote = self._detect_remote(location_str, raw_item)
        description = raw_item.get("content") or raw_item.get("description") or ""

        # Extract skills from description
        skills = self.extract_skills_from_text(description)

        # Parse posting date
        posted_at = self._parse_date(raw_item.get("updated_at") or raw_item.get("created_at") or raw_item.get("posted_at"))

        posting_url = raw_item.get("absolute_url") or raw_item.get("url") or raw_item.get("link")
        external_id = str(raw_item.get("id") or raw_item.get("job_id") or "")

        return RawJobData(
            title=title,
            company_name=company,
            source_type=self.provider_name,
            location=location_str if location_str else None,
            is_remote=is_remote,
            country=self._extract_country(location_str),
            description=description if description else None,
            employment_type=raw_item.get("employment_type", "full-time"),
            posting_url=posting_url,
            apply_url=posting_url,
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
        if any(term in loc_lower for term in ["remote", "wfh", "anywhere", "distributed"]):
            return True
        title_lower = (raw.get("title") or "").lower()
        return "remote" in title_lower

    def _extract_country(self, location: str) -> str | None:
        """Extract country from location string."""
        if not location:
            return None
        parts = [p.strip() for p in location.split(",")]
        return parts[-1] if parts else None

    def _parse_date(self, date_val: Any) -> datetime | None:
        """Parse datetime string into datetime object."""
        if not date_val:
            return None
        if isinstance(date_val, datetime):
            return date_val
        try:
            return datetime.fromisoformat(str(date_val).replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
