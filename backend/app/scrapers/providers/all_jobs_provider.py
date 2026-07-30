"""
HuntIQ — All Jobs Multi-Platform Provider.

Scrapes 39+ job platforms simultaneously using the agentx/all-jobs-scraper Apify actor.
Covers: LinkedIn, Indeed, Glassdoor, Naukri, Wellfound, ZipRecruiter, Monster, Lever,
Greenhouse, Ashby, Workable, RemoteOK, WeWorkRemotely, and 26+ more.

Actor: agentx/all-jobs-scraper
Docs: https://apify.com/agentx/all-jobs-scraper
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
class AllJobsProvider(JobProvider):
    """Multi-platform job scraper using agentx/all-jobs-scraper (39 platforms)."""

    provider_name = "all_jobs"
    actor_id = "agentx/all-jobs-scraper"

    default_memory_mbytes = 512
    default_timeout_secs = 600

    def build_actor_input(self, search_input: SearchInput) -> dict[str, Any]:
        """
        Build actor input for the all-jobs-scraper.

        The actor accepts: keyword, country, max_results, remote_only.
        We run one combined keyword from the search input.
        """
        keyword = " ".join(search_input.keywords[:2]) if search_input.keywords else "Software Engineer"
        country = search_input.locations[0] if search_input.locations else "India"

        return {
            "keyword": keyword,
            "country": country,
            "max_results": search_input.max_results,
        }

    def parse_result(self, raw_item: dict[str, Any]) -> RawJobData | None:
        """
        Parse a standardized result from the all-jobs-scraper actor.

        The actor returns a unified schema with fields like:
        title, company, location, url, salary_min, salary_max,
        description, skills, source_platform, posted_date, etc.
        """
        title = (raw_item.get("title") or raw_item.get("job_title") or "").strip()
        company = (raw_item.get("company") or raw_item.get("company_name") or "").strip()

        if not title or not company:
            return None

        # Extract the real job posting URL
        posting_url = (
            raw_item.get("url")
            or raw_item.get("job_url")
            or raw_item.get("link")
            or raw_item.get("posting_url")
        )
        apply_url = (
            raw_item.get("apply_url")
            or raw_item.get("apply_link")
            or posting_url
        )

        # Location & remote detection
        location = raw_item.get("location") or raw_item.get("job_location") or ""
        is_remote = self._detect_remote(location, raw_item)

        # Source platform (linkedin, indeed, naukri, glassdoor, etc.)
        source = (
            raw_item.get("source_platform")
            or raw_item.get("source")
            or raw_item.get("platform")
            or "all_jobs"
        )

        # Salary
        salary_min = self._safe_int(raw_item.get("salary_min") or raw_item.get("min_salary"))
        salary_max = self._safe_int(raw_item.get("salary_max") or raw_item.get("max_salary"))
        salary_currency = raw_item.get("salary_currency") or raw_item.get("currency")

        # Experience
        exp_min = self._safe_int(raw_item.get("experience_min") or raw_item.get("min_experience"))
        exp_max = self._safe_int(raw_item.get("experience_max") or raw_item.get("max_experience"))
        seniority = raw_item.get("seniority_level") or raw_item.get("experience_level")

        # Skills
        skills_raw = raw_item.get("skills") or raw_item.get("required_skills") or []
        if isinstance(skills_raw, str):
            skills_raw = [s.strip() for s in skills_raw.split(",") if s.strip()]

        # Description
        description = raw_item.get("description") or raw_item.get("job_description") or ""

        # Extract additional skills from description
        desc_skills = self.extract_skills_from_text(description)
        all_skills = sorted(set(skills_raw + desc_skills))

        # Posted date
        posted_at = self._parse_date(
            raw_item.get("posted_date")
            or raw_item.get("posted_at")
            or raw_item.get("date_posted")
        )

        # Country
        country = raw_item.get("country") or self._extract_country(location)

        return RawJobData(
            title=title,
            company_name=company,
            source_type=source.lower(),
            location=location if location else None,
            is_remote=is_remote,
            country=country,
            description=description if description else None,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            salary_period="yearly",
            experience_min=exp_min,
            experience_max=exp_max,
            seniority_level=seniority,
            employment_type=raw_item.get("employment_type") or raw_item.get("job_type") or "full-time",
            posting_url=posting_url,
            apply_url=apply_url,
            external_id=raw_item.get("id") or raw_item.get("job_id") or raw_item.get("external_id"),
            skills=all_skills,
            tech_stack=all_skills,
            company_website=raw_item.get("company_url") or raw_item.get("company_website"),
            company_logo_url=raw_item.get("company_logo") or raw_item.get("logo_url"),
            company_industry=raw_item.get("industry") or raw_item.get("company_industry"),
            company_size=raw_item.get("company_size"),
            posted_at=posted_at,
            raw_data=raw_item,
        )

    def _detect_remote(self, location: str, raw: dict[str, Any]) -> bool:
        """Detect if a job is remote from location and raw data."""
        if not location:
            return raw.get("remote", False) or raw.get("is_remote", False)
        loc_lower = location.lower()
        remote_indicators = {"remote", "work from home", "wfh", "anywhere", "hybrid", "distributed"}
        if any(ind in loc_lower for ind in remote_indicators):
            return True
        return raw.get("remote", False) or raw.get("is_remote", False)

    def _extract_country(self, location: str) -> str | None:
        """Extract country from location string."""
        if not location:
            return None
        loc_lower = location.lower()
        country_map = {
            "india": "India", "bengaluru": "India", "bangalore": "India",
            "hyderabad": "India", "gurgaon": "India", "gurugram": "India",
            "mumbai": "India", "pune": "India", "chennai": "India",
            "noida": "India", "delhi": "India", "kolkata": "India",
            "united states": "United States", "usa": "United States",
            "united kingdom": "United Kingdom", "uk": "United Kingdom",
            "germany": "Germany", "singapore": "Singapore",
            "canada": "Canada", "australia": "Australia",
            "remote": "Remote",
        }
        for key, country in country_map.items():
            if key in loc_lower:
                return country
        return None

    def _safe_int(self, val: Any) -> int | None:
        """Safely convert a value to int."""
        if val is None:
            return None
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None

    def _parse_date(self, date_val: Any) -> datetime | None:
        """Parse various date formats."""
        if not date_val:
            return None
        if isinstance(date_val, datetime):
            return date_val

        if isinstance(date_val, str):
            # Try ISO format
            for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                try:
                    return datetime.strptime(date_val.split(".")[0].split("Z")[0], fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            # Try ISO with timezone
            try:
                return datetime.fromisoformat(date_val.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        return None
