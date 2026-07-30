"""
HuntIQ — Wellfound (AngelList) Job Provider.

Scrapes Wellfound startup job listings via Apify's Wellfound scraper actor.
Handles startup-specific data schemas (equity, company size, stage) and maps them to RawJobData.

Actor: apify/wellfound-jobs-scraper
Docs: https://apify.com/apify/wellfound-jobs-scraper
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
class WellfoundProvider(JobProvider):
    """Wellfound (AngelList) job scraper using Apify."""

    provider_name = "wellfound"
    actor_id = "apify/wellfound-jobs-scraper"

    default_memory_mbytes = 512
    default_timeout_secs = 400

    def build_actor_input(self, search_input: SearchInput) -> dict[str, Any]:
        """
        Build Wellfound-specific Apify actor input.

        Maps generic search parameters to the wellfound-jobs-scraper schema.
        """
        keywords = search_input.keywords or ["Backend Engineer"]
        locations = search_input.locations or []

        return {
            "roleKeywords": keywords,
            "locations": locations,
            "maxItems": search_input.max_results,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            },
        }

    def parse_result(self, raw_item: dict[str, Any]) -> RawJobData | None:
        """
        Parse a single Wellfound job listing into RawJobData.

        Wellfound items typically include:
        id, title, company/startupName, location/locations,
        remote, salaryRange, equityRange, companySize, logoUrl,
        jobUrl, description, postedDate, etc.
        """
        title = (raw_item.get("title") or raw_item.get("role") or "").strip()
        company = (
            raw_item.get("company")
            or raw_item.get("startupName")
            or raw_item.get("companyName")
            or ""
        ).strip()

        if not title:
            return None

        if not company:
            company = "Startup"

        # Location parsing (Wellfound returns list or string)
        loc_data = raw_item.get("locations") or raw_item.get("location") or ""
        if isinstance(loc_data, list):
            location_str = ", ".join(str(loc) for loc in loc_data if loc)
        else:
            location_str = str(loc_data).strip()

        is_remote = bool(raw_item.get("remote")) or self._detect_remote(location_str, raw_item)

        salary_min, salary_max, currency = self._parse_salary(raw_item.get("salaryRange") or raw_item.get("salary"))

        description = raw_item.get("description") or raw_item.get("details") or ""
        skills = self.extract_skills_from_text(description)

        # Wellfound tags often include explicit tech stack
        tags = raw_item.get("tags") or raw_item.get("skills") or []
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, str) and tag.strip():
                    skills.append(tag.strip().lower())
            skills = sorted(set(skills))

        posted_at = self._parse_date(raw_item.get("postedDate") or raw_item.get("createdAt") or raw_item.get("postedAt"))

        posting_url = raw_item.get("jobUrl") or raw_item.get("url") or raw_item.get("link")
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
            salary_period="yearly",
            employment_type=raw_item.get("type", "full-time"),
            posting_url=posting_url,
            apply_url=apply_url,
            external_id=external_id if external_id else None,
            skills=skills,
            tech_stack=skills,
            company_website=raw_item.get("companyWebsite"),
            company_logo_url=raw_item.get("logoUrl") or raw_item.get("companyLogo"),
            company_size=raw_item.get("companySize"),
            posted_at=posted_at,
            raw_data=raw_item,
        )

    def _detect_remote(self, location: str, raw: dict[str, Any]) -> bool:
        """Detect if job is remote."""
        if raw.get("remote"):
            return True
        if not location:
            return False
        loc_lower = location.lower()
        return any(term in loc_lower for term in ["remote", "wfh", "anywhere"])

    def _parse_salary(self, salary_val: Any) -> tuple[int | None, int | None, str | None]:
        """Parse Wellfound salary string or dict (e.g. '$100k – $150k')."""
        if not salary_val:
            return None, None, None

        if isinstance(salary_val, dict):
            return (
                salary_val.get("min"),
                salary_val.get("max"),
                salary_val.get("currency", "USD"),
            )

        salary_str = str(salary_val)
        import re

        numbers = re.findall(r"[\d,.]+", salary_str)
        if not numbers:
            return None, None, "USD"

        parsed: list[int] = []
        for num_str in numbers:
            num_str = num_str.replace(",", "")
            try:
                val = float(num_str)
                if "k" in salary_str.lower() and val < 1000:
                    val *= 1000
                parsed.append(int(val))
            except ValueError:
                continue

        if len(parsed) >= 2:
            return parsed[0], parsed[1], "USD"
        if len(parsed) == 1:
            return parsed[0], None, "USD"
        return None, None, "USD"

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
