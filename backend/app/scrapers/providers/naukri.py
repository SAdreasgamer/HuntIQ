"""
HuntIQ — Naukri Job Provider.

Scrapes Naukri (India job portal) listings via Apify's Naukri scraper actor.
Handles Naukri-specific schemas (Lakh salary ranges, experience years, keySkills) and maps them to RawJobData.

Actor: apify/naukri-scraper
Docs: https://apify.com/apify/naukri-scraper
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
class NaukriProvider(JobProvider):
    """Naukri job scraper using Apify."""

    provider_name = "naukri"
    actor_id = "apify/naukri-scraper"

    default_memory_mbytes = 512
    default_timeout_secs = 450

    def build_actor_input(self, search_input: SearchInput) -> dict[str, Any]:
        """
        Build Naukri-specific Apify actor input.

        Maps generic search parameters to the naukri-scraper schema.
        """
        keywords = search_input.keywords or ["Backend Engineer"]
        locations = search_input.locations or ["India"]

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
        Parse a single Naukri job listing into RawJobData.

        Naukri items typically include:
        jobId/id, title, companyName, location/place,
        experienceStr/experience, salaryStr/salary,
        keySkills/tags, jobDescription/description, createdDate, url, etc.
        """
        title = (raw_item.get("title") or raw_item.get("jobTitle") or "").strip()
        company = (
            raw_item.get("companyName")
            or raw_item.get("company")
            or ""
        ).strip()

        if not title:
            return None

        if not company:
            company = "Naukri Employer"

        location_str = str(raw_item.get("location") or raw_item.get("place") or "India").strip()
        is_remote = self._detect_remote(location_str, raw_item)

        # Parse experience (e.g. "2-5 Yrs", "0-2 years")
        exp_min, exp_max = self._parse_experience(raw_item.get("experienceStr") or raw_item.get("experience"))

        # Parse salary (e.g. "12-25 PA", "15-30 Lacs PA", "Not disclosed")
        salary_min, salary_max = self._parse_salary_inr(raw_item.get("salaryStr") or raw_item.get("salary"))

        description = raw_item.get("jobDescription") or raw_item.get("description") or ""
        skills = self.extract_skills_from_text(description)

        # Naukri provides explicit keySkills list
        key_skills = raw_item.get("keySkills") or raw_item.get("tags") or []
        if isinstance(key_skills, list):
            for skill in key_skills:
                if isinstance(skill, str) and skill.strip():
                    skills.append(skill.strip().lower())
            skills = sorted(set(skills))

        posted_at = self._parse_date(raw_item.get("createdDate") or raw_item.get("postedDate") or raw_item.get("date"))

        posting_url = raw_item.get("url") or raw_item.get("jobUrl") or raw_item.get("link")
        external_id = str(raw_item.get("jobId") or raw_item.get("id") or "")

        return RawJobData(
            title=title,
            company_name=company,
            source_type=self.provider_name,
            location=location_str,
            is_remote=is_remote,
            country="India",
            description=description if description else None,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency="INR",
            salary_period="yearly",
            experience_min=exp_min,
            experience_max=exp_max,
            employment_type="full-time",
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
        if any(term in loc_lower for term in ["remote", "work from home", "wfh", "anywhere"]):
            return True
        title_lower = (raw.get("title") or "").lower()
        return "remote" in title_lower or "wfh" in title_lower

    def _parse_experience(self, exp_val: Any) -> tuple[int | None, int | None]:
        """Parse Naukri experience string (e.g., '2-5 Yrs', '3 to 6 yrs')."""
        if not exp_val:
            return None, None

        exp_str = str(exp_val)
        import re

        numbers = re.findall(r"\d+", exp_str)
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        if len(numbers) == 1:
            return int(numbers[0]), int(numbers[0])
        return None, None

    def _parse_salary_inr(self, salary_val: Any) -> tuple[int | None, int | None]:
        """
        Parse Naukri INR salary string into integer annual INR values.

        Handles formats like:
        - "12-25 PA" or "12-25 Lacs PA" -> 1,200,000 to 2,500,000 INR
        - "15,00,000 - 25,00,000 PA" -> 1,500,000 to 2,500,000 INR
        """
        if not salary_val:
            return None, None

        salary_str = str(salary_val).lower()
        if "not disclosed" in salary_str or "undisclosed" in salary_str:
            return None, None

        import re

        numbers = re.findall(r"[\d.]+", salary_str.replace(",", ""))
        if not numbers:
            return None, None

        parsed: list[int] = []
        for num_str in numbers:
            try:
                val = float(num_str)
                # If numbers are small (< 100), assume Lakhs
                if val < 100:
                    val *= 100000
                parsed.append(int(val))
            except ValueError:
                continue

        if len(parsed) >= 2:
            return parsed[0], parsed[1]
        if len(parsed) == 1:
            return parsed[0], None
        return None, None

    def _parse_date(self, date_val: Any) -> datetime | None:
        """Parse datetime or relative date string."""
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
