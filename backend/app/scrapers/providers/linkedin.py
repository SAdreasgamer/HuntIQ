"""
HuntIQ — LinkedIn Job Provider.

Scrapes LinkedIn job listings via Apify's LinkedIn Jobs Scraper actor.
Handles the LinkedIn-specific data format and maps it to RawJobData.

Actor: apify/linkedin-jobs-scraper
Docs: https://apify.com/apify/linkedin-jobs-scraper
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
class LinkedInProvider(JobProvider):
    """LinkedIn job scraper using Apify."""

    provider_name = "linkedin"
    actor_id = "hMvNSpz3JnHgl5jkh"  # apify/linkedin-jobs-scraper

    default_memory_mbytes = 512
    default_timeout_secs = 600

    def build_actor_input(self, search_input: SearchInput) -> dict[str, Any]:
        """
        Build LinkedIn-specific Apify actor input.

        Maps generic search params to the linkedin-jobs-scraper
        actor's input schema.
        """
        # Build search URL queries
        queries: list[dict[str, Any]] = []
        for keyword in search_input.keywords:
            for location in search_input.locations or [""]:
                query: dict[str, Any] = {
                    "keyword": keyword,
                    "location": location,
                }
                queries.append(query)

        return {
            "queries": queries,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            },
            "maxItems": search_input.max_results,
            "parseCompanyDetails": True,
            "saveOnlyUniqueItems": True,
        }

    def parse_result(self, raw_item: dict[str, Any]) -> RawJobData | None:
        """
        Parse a single LinkedIn job listing into RawJobData.

        LinkedIn actor returns items with fields like:
        title, companyName, location, description, link,
        applyLink, salary, postedAt, companyUrl, etc.
        """
        title = raw_item.get("title", "").strip()
        company = raw_item.get("companyName", "").strip()

        # Skip items without title or company
        if not title or not company:
            return None

        # Parse location and remote status
        location = raw_item.get("location", "")
        is_remote = self._detect_remote(location, raw_item)

        # Parse salary info
        salary_min, salary_max, currency = self._parse_salary(
            raw_item.get("salary", "")
        )

        # Parse experience level
        exp_level = raw_item.get("experienceLevel", "")
        exp_min, exp_max = self._parse_experience(exp_level)
        seniority = self._map_seniority(exp_level)

        # Parse posting date
        posted_at = self._parse_date(raw_item.get("postedAt"))

        # Extract skills from description
        description = raw_item.get("description", "")
        skills = self.extract_skills_from_text(description)

        return RawJobData(
            title=title,
            company_name=company,
            source_type=self.provider_name,
            location=location if location else None,
            is_remote=is_remote,
            country=self._extract_country(location),
            description=description if description else None,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=currency,
            salary_period="yearly",
            experience_min=exp_min,
            experience_max=exp_max,
            seniority_level=seniority,
            employment_type=raw_item.get("contractType", "full-time"),
            posting_url=raw_item.get("link"),
            apply_url=raw_item.get("applyLink") or raw_item.get("link"),
            external_id=raw_item.get("jobId") or raw_item.get("id"),
            skills=skills,
            tech_stack=skills,
            company_website=raw_item.get("companyUrl"),
            company_logo_url=raw_item.get("companyLogo"),
            company_industry=raw_item.get("companyIndustry"),
            company_size=raw_item.get("companySize"),
            posted_at=posted_at,
            raw_data=raw_item,
        )

    # ==============================================================
    # LinkedIn-Specific Parsing Helpers
    # ==============================================================

    def _detect_remote(self, location: str, raw: dict[str, Any]) -> bool:
        """Detect if a LinkedIn job is remote."""
        if not location:
            return False
        location_lower = location.lower()
        remote_indicators = {"remote", "work from home", "wfh", "anywhere", "hybrid"}
        if any(indicator in location_lower for indicator in remote_indicators):
            return True
        workplace_type = raw.get("workplaceType", "").lower()
        return workplace_type in {"remote", "hybrid"}

    def _parse_salary(self, salary_str: str) -> tuple[int | None, int | None, str | None]:
        """
        Parse LinkedIn salary string into (min, max, currency).

        Handles formats like:
        - "$120K - $180K"
        - "₹15L - ₹25L"
        - "$50/hr"
        """
        if not salary_str:
            return None, None, None

        import re

        # Detect currency
        currency = "USD"
        if "₹" in salary_str or "INR" in salary_str:
            currency = "INR"
        elif "€" in salary_str or "EUR" in salary_str:
            currency = "EUR"
        elif "£" in salary_str or "GBP" in salary_str:
            currency = "GBP"
        elif "S$" in salary_str or "SGD" in salary_str:
            currency = "SGD"

        # Extract numbers
        numbers = re.findall(r"[\d,.]+", salary_str)
        if not numbers:
            return None, None, currency

        parsed_numbers: list[int] = []
        for num_str in numbers:
            num_str = num_str.replace(",", "")
            try:
                num = float(num_str)
                # Handle K suffix
                if "k" in salary_str.lower():
                    num *= 1000
                # Handle L (lakh) suffix
                if "l" in salary_str.lower() and currency == "INR":
                    num *= 100000
                parsed_numbers.append(int(num))
            except ValueError:
                continue

        if len(parsed_numbers) >= 2:
            return parsed_numbers[0], parsed_numbers[1], currency
        if len(parsed_numbers) == 1:
            return parsed_numbers[0], None, currency
        return None, None, currency

    def _parse_experience(self, exp_level: str) -> tuple[int | None, int | None]:
        """Map LinkedIn experience level to year ranges."""
        exp_map: dict[str, tuple[int | None, int | None]] = {
            "internship": (0, 0),
            "entry level": (0, 2),
            "associate": (1, 3),
            "mid-senior level": (3, 7),
            "director": (7, 15),
            "executive": (10, None),
        }
        return exp_map.get(exp_level.lower(), (None, None))

    def _map_seniority(self, exp_level: str) -> str | None:
        """Map LinkedIn experience level to seniority."""
        seniority_map: dict[str, str] = {
            "internship": "intern",
            "entry level": "entry",
            "associate": "mid",
            "mid-senior level": "senior",
            "director": "lead",
            "executive": "lead",
        }
        return seniority_map.get(exp_level.lower())

    def _extract_country(self, location: str) -> str | None:
        """Extract country from LinkedIn location string."""
        if not location:
            return None

        # LinkedIn often includes country at the end
        parts = [p.strip() for p in location.split(",")]
        if len(parts) >= 2:
            potential_country = parts[-1]
            known_countries = {
                "India", "United States", "United Kingdom", "Germany",
                "Singapore", "Netherlands", "Ireland", "Canada",
                "Australia", "France", "Japan", "Remote",
            }
            for country in known_countries:
                if country.lower() in potential_country.lower():
                    return country
        return parts[-1] if parts else None

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse LinkedIn date strings into datetime."""
        if not date_str:
            return None

        # Try ISO format first
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

        # Try relative date parsing (e.g., "2 days ago", "1 week ago")
        date_lower = date_str.lower()
        now = datetime.now(timezone.utc)

        import re
        from datetime import timedelta

        match = re.search(r"(\d+)\s*(minute|hour|day|week|month)s?\s*ago", date_lower)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            delta_map: dict[str, timedelta] = {
                "minute": timedelta(minutes=amount),
                "hour": timedelta(hours=amount),
                "day": timedelta(days=amount),
                "week": timedelta(weeks=amount),
                "month": timedelta(days=amount * 30),
            }
            delta = delta_map.get(unit)
            if delta:
                return now - delta

        return None
