"""
HuntIQ — Ashby Job Provider.

Scrapes Ashby ATS job boards via Apify's Ashby scraper actor.
Handles Ashby-specific data schemas and maps them to RawJobData.

Actor: apify/ashby-scraper
Docs: https://apify.com/apify/ashby-scraper
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
class AshbyProvider(JobProvider):
    """Ashby ATS job scraper using Apify."""

    provider_name = "ashby"
    actor_id = "apify/ashby-scraper"

    default_memory_mbytes = 256
    default_timeout_secs = 300

    def build_actor_input(self, search_input: SearchInput) -> dict[str, Any]:
        """
        Build Ashby-specific Apify actor input.

        Maps generic search parameters to the ashby actor's input schema.
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
        Parse a single Ashby job listing into RawJobData.

        Ashby items typically include:
        id, title, companyName/company, location/locationName,
        isRemote, employmentType, compensation, jobUrl/applyUrl,
        descriptionParts/description, publishedAt, etc.
        """
        title = (raw_item.get("title") or raw_item.get("jobTitle") or "").strip()
        company = (
            raw_item.get("companyName")
            or raw_item.get("company")
            or raw_item.get("company_name")
            or ""
        ).strip()

        if not title:
            return None

        if not company:
            company = "Ashby Company"

        location_str = str(raw_item.get("locationName") or raw_item.get("location") or "").strip()
        is_remote = bool(raw_item.get("isRemote")) or self._detect_remote(location_str, raw_item)

        description = raw_item.get("description") or raw_item.get("descriptionHtml") or ""
        skills = self.extract_skills_from_text(description)

        salary_min, salary_max, currency = self._parse_compensation(raw_item.get("compensation"))

        posted_at = self._parse_date(raw_item.get("publishedAt") or raw_item.get("createdAt") or raw_item.get("postedAt"))

        posting_url = raw_item.get("jobUrl") or raw_item.get("url") or raw_item.get("applyUrl")
        apply_url = raw_item.get("applyUrl") or posting_url
        external_id = str(raw_item.get("id") or raw_item.get("jobId") or "")

        return RawJobData(
            title=title,
            company_name=company,
            source_type=self.provider_name,
            location=location_str if location_str else None,
            is_remote=is_remote,
            country=self._extract_country(location_str),
            description=description if description else None,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=currency,
            employment_type=str(raw_item.get("employmentType") or "full-time").lower(),
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
        if raw.get("isRemote"):
            return True
        if not location:
            return False
        loc_lower = location.lower()
        return any(term in loc_lower for term in ["remote", "wfh", "anywhere", "distributed"])

    def _extract_country(self, location: str) -> str | None:
        """Extract country from location string."""
        if not location:
            return None
        parts = [p.strip() for p in location.split(",")]
        return parts[-1] if parts else None

    def _parse_compensation(self, comp: Any) -> tuple[int | None, int | None, str | None]:
        """Parse Ashby compensation object or string."""
        if not comp:
            return None, None, None
        if isinstance(comp, dict):
            min_val = comp.get("minValue") or comp.get("min")
            max_val = comp.get("maxValue") or comp.get("max")
            currency = comp.get("currencyCode") or comp.get("currency") or "USD"
            return (
                int(min_val) if min_val is not None else None,
                int(max_val) if max_val is not None else None,
                str(currency),
            )
        return None, None, None

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
