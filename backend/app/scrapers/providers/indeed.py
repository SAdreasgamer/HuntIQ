"""
HuntIQ — Indeed Job Provider.

Scrapes Indeed job listings via Apify's Indeed scraper actor.
Handles Indeed-specific data schemas and maps them to RawJobData.

Actor: apify/indeed-scraper
Docs: https://apify.com/apify/indeed-scraper
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
class IndeedProvider(JobProvider):
    """Indeed job scraper using Apify."""

    provider_name = "indeed"
    actor_id = "apify/indeed-scraper"

    default_memory_mbytes = 512
    default_timeout_secs = 450

    def build_actor_input(self, search_input: SearchInput) -> dict[str, Any]:
        """
        Build Indeed-specific Apify actor input.

        Maps generic search parameters to the indeed-scraper input schema.
        """
        keywords = search_input.keywords or ["backend engineer"]
        locations = search_input.locations or [""]

        # Prepare queries array
        queries = []
        for kw in keywords:
            for loc in locations:
                queries.append({
                    "keyword": kw,
                    "location": loc,
                })

        return {
            "queries": queries,
            "maxItems": search_input.max_results,
            "country": "us",
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            },
        }

    def parse_result(self, raw_item: dict[str, Any]) -> RawJobData | None:
        """
        Parse a single Indeed job listing into RawJobData.

        Indeed items typically include:
        id/jobId, positionName/title, company, location, isRemote,
        salary, jobType, description, url, postedAt, companyRating, etc.
        """
        title = (
            raw_item.get("positionName")
            or raw_item.get("title")
            or raw_item.get("jobTitle")
            or ""
        ).strip()
        company = (
            raw_item.get("company")
            or raw_item.get("companyName")
            or ""
        ).strip()

        if not title:
            return None

        if not company:
            company = "Indeed Employer"

        location_str = str(raw_item.get("location") or raw_item.get("formattedLocation") or "").strip()
        is_remote = bool(raw_item.get("isRemote")) or self._detect_remote(location_str, raw_item)

        salary_min, salary_max, currency = self._parse_salary(raw_item.get("salary") or raw_item.get("salaryText"))

        description = raw_item.get("description") or raw_item.get("jobDescription") or ""
        skills = self.extract_skills_from_text(description)

        posted_at = self._parse_date(raw_item.get("postedAt") or raw_item.get("postDate") or raw_item.get("date"))

        posting_url = raw_item.get("url") or raw_item.get("jobUrl") or raw_item.get("link")
        external_id = str(raw_item.get("id") or raw_item.get("jobId") or raw_item.get("key") or "")

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
            employment_type=str(raw_item.get("jobType") or "full-time").lower(),
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
        if raw.get("isRemote"):
            return True
        if not location:
            return False
        loc_lower = location.lower()
        return any(term in loc_lower for term in ["remote", "work from home", "wfh", "anywhere"])

    def _parse_salary(self, salary_val: Any) -> tuple[int | None, int | None, str | None]:
        """Parse Indeed salary string or dict (e.g. '$120,000 - $160,000 a year')."""
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

        currency = "USD"
        if "₹" in salary_str or "INR" in salary_str:
            currency = "INR"
        elif "€" in salary_str or "EUR" in salary_str:
            currency = "EUR"
        elif "£" in salary_str or "GBP" in salary_str:
            currency = "GBP"

        numbers = re.findall(r"[\d,.]+", salary_str)
        if not numbers:
            return None, None, currency

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
            return parsed[0], parsed[1], currency
        if len(parsed) == 1:
            return parsed[0], None, currency
        return None, None, currency

    def _extract_country(self, location: str) -> str | None:
        """Extract country from location string."""
        if not location:
            return None
        parts = [p.strip() for p in location.split(",")]
        return parts[-1] if parts else None

    def _parse_date(self, date_val: Any) -> datetime | None:
        """Parse datetime string or relative date into datetime object."""
        if not date_val:
            return None
        if isinstance(date_val, datetime):
            return date_val

        date_str = str(date_val).lower()
        now = datetime.now(timezone.utc)

        import re
        from datetime import timedelta

        match = re.search(r"(\d+)\s*(day|hour|week|month)s?\s*ago", date_str)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            delta_map: dict[str, timedelta] = {
                "hour": timedelta(hours=amount),
                "day": timedelta(days=amount),
                "week": timedelta(weeks=amount),
                "month": timedelta(days=amount * 30),
            }
            delta = delta_map.get(unit)
            if delta:
                return now - delta

        try:
            return datetime.fromisoformat(date_str.replace("z", "+00:00"))
        except (ValueError, AttributeError):
            return None
