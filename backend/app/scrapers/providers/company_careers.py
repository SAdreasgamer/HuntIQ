"""
HuntIQ — Company Careers Provider.

Scrapes custom company career pages and direct career portals via Apify's web scraper.
Handles arbitrary company career page outputs and maps them to RawJobData.

Actor: apify/company-careers-scraper
Docs: https://apify.com/apify/company-careers-scraper
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
class CompanyCareersProvider(JobProvider):
    """Direct company career page scraper using Apify."""

    provider_name = "company_careers"
    actor_id = "apify/company-careers-scraper"

    default_memory_mbytes = 512
    default_timeout_secs = 600

    def build_actor_input(self, search_input: SearchInput) -> dict[str, Any]:
        """
        Build Company Careers-specific Apify actor input.

        Maps generic search parameters and target company career URLs to the actor input.
        """
        keywords = search_input.keywords or ["Backend Engineer"]
        locations = search_input.locations or []

        return {
            "searchKeywords": keywords,
            "locations": locations,
            "maxItems": search_input.max_results,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            },
        }

    def parse_result(self, raw_item: dict[str, Any]) -> RawJobData | None:
        """
        Parse a single direct company career page item into RawJobData.

        Career page items typically include:
        title/role, company/companyName, location, description/body,
        url/link, postedAt, employmentType, department, etc.
        """
        title = (
            raw_item.get("title")
            or raw_item.get("role")
            or raw_item.get("position")
            or ""
        ).strip()
        company = (
            raw_item.get("company")
            or raw_item.get("companyName")
            or raw_item.get("company_name")
            or ""
        ).strip()

        if not title:
            return None

        if not company:
            company = "Target Company"

        location_str = str(raw_item.get("location") or raw_item.get("office") or "").strip()
        is_remote = bool(raw_item.get("isRemote")) or self._detect_remote(location_str, raw_item)

        description = raw_item.get("description") or raw_item.get("content") or raw_item.get("body") or ""
        skills = self.extract_skills_from_text(description)

        posted_at = self._parse_date(raw_item.get("postedAt") or raw_item.get("createdAt") or raw_item.get("date"))

        posting_url = raw_item.get("url") or raw_item.get("link") or raw_item.get("applyUrl")
        apply_url = raw_item.get("applyUrl") or posting_url
        external_id = str(raw_item.get("id") or raw_item.get("jobId") or raw_item.get("slug") or "")

        return RawJobData(
            title=title,
            company_name=company,
            source_type=self.provider_name,
            location=location_str if location_str else None,
            is_remote=is_remote,
            country=self._extract_country(location_str),
            description=description if description else None,
            employment_type=str(raw_item.get("employmentType") or raw_item.get("type") or "full-time").lower(),
            posting_url=posting_url,
            apply_url=apply_url,
            external_id=external_id if external_id else None,
            skills=skills,
            tech_stack=skills,
            company_website=raw_item.get("companyWebsite") or raw_item.get("website"),
            posted_at=posted_at,
            raw_data=raw_item,
        )

    def _detect_remote(self, location: str, raw: dict[str, Any]) -> bool:
        """Detect if job is remote."""
        if raw.get("isRemote"):
            return True
        if not location:
            return False
        loc_lower = location.lower()
        return any(term in loc_lower for term in ["remote", "work from home", "wfh", "anywhere", "distributed"])

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
