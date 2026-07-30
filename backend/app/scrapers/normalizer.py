"""
HuntIQ — Job Normalization and Deduplication Engine.

Transforms provider RawJobData into normalized database records:
- Job ORM model
- Company ORM model (with deduplication via normalized_name)
- JobSkill ORM records
- JobSource ORM record (tracking raw provider response and URLs)

Deduplication rules:
1. Exact content_hash match (SHA-256 of company + title + description snippet)
2. Fuzzy company_id + title + posting_url match -> marks duplicate_of_id
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.job import Job, JobSkill, JobSource
from app.repositories.company import CompanyRepository
from app.repositories.job import (
    JobRepository,
    JobSkillRepository,
    JobSourceRepository,
)
from app.scrapers.schemas import RawJobData

logger = get_logger(__name__)


class JobNormalizer:
    """Service that ingests RawJobData and persists normalized DB models."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize normalizer with database session.

        Args:
            session: Async database session.
        """
        self.session = session
        self.company_repo = CompanyRepository(session)
        self.job_repo = JobRepository(session)
        self.skill_repo = JobSkillRepository(session)
        self.source_repo = JobSourceRepository(session)

    def compute_content_hash(self, company_name: str, title: str, description: str | None) -> str:
        """
        Compute SHA-256 content hash for exact deduplication.

        Hash string format: 'company|title|description_prefix'
        """
        norm_company = company_name.strip().lower()
        norm_title = title.strip().lower()
        desc_snippet = (description or "")[:300].strip().lower()

        raw_str = f"{norm_company}|{norm_title}|{desc_snippet}"
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    async def normalize_and_save(self, raw_job: RawJobData) -> tuple[Job, bool]:
        """
        Process a RawJobData instance into database records.

        Args:
            raw_job: Raw scraped job schema.

        Returns:
            Tuple of (Job ORM model, is_new boolean).
        """
        # 1. Get or create Company
        company, _ = await self.company_repo.get_or_create(
            name=raw_job.company_name,
            website=raw_job.company_website,
            logo_url=raw_job.company_logo_url,
            industry=raw_job.company_industry,
            employee_count=raw_job.company_size,
        )

        # 2. Compute Content Hash
        content_hash = self.compute_content_hash(
            company_name=raw_job.company_name,
            title=raw_job.title,
            description=raw_job.description,
        )

        # 3. Check for exact duplicate via content_hash
        existing_job = await self.job_repo.get_by_content_hash(content_hash)
        if existing_job:
            # Update last_seen_at timestamp
            existing_job.last_seen_at = datetime.now(timezone.utc)

            # Ensure JobSource record exists for this provider
            await self._ensure_job_source(existing_job.id, raw_job)
            await self.session.flush()

            logger.info(
                "job_dedup_exact_hash_match",
                job_id=existing_job.id,
                title=existing_job.title,
                provider=raw_job.source_type,
            )
            return existing_job, False

        # 4. Check for fuzzy duplicates (same company + title + posting_url)
        duplicates = await self.job_repo.find_duplicates(
            company_id=company.id,
            title=raw_job.title,
            posting_url=raw_job.posting_url,
        )

        is_duplicate = len(duplicates) > 0
        duplicate_of_id = duplicates[0].id if is_duplicate else None

        # Normalize salary period
        salary_min, salary_max = self._normalize_salary(
            raw_job.salary_min,
            raw_job.salary_max,
            raw_job.salary_period,
        )

        # 5. Create Job Record
        job = await self.job_repo.create(
            title=raw_job.title.strip(),
            company_id=company.id,
            description=raw_job.description,
            requirements=raw_job.requirements,
            responsibilities=raw_job.responsibilities,
            location=raw_job.location,
            is_remote=raw_job.is_remote,
            country=raw_job.country,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=raw_job.salary_currency or "USD",
            salary_period="yearly",
            experience_min=raw_job.experience_min,
            experience_max=raw_job.experience_max,
            seniority_level=raw_job.seniority_level,
            employment_type=raw_job.employment_type or "full-time",
            posting_url=raw_job.posting_url,
            apply_url=raw_job.apply_url or raw_job.posting_url,
            external_id=raw_job.external_id,
            tech_stack=raw_job.tech_stack,
            content_hash=content_hash,
            posted_at=raw_job.posted_at or datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
            is_active=True,
            is_duplicate=is_duplicate,
            duplicate_of_id=duplicate_of_id,
        )

        # 6. Create JobSkill Records
        skills_to_create = set(raw_job.skills + raw_job.tech_stack)
        skill_records = [
            {
                "job_id": job.id,
                "skill_name": skill.strip().lower(),
                "is_required": True,
            }
            for skill in skills_to_create
            if skill.strip()
        ]
        if skill_records:
            await self.skill_repo.bulk_create(skill_records)

        # 7. Create JobSource Record
        await self._ensure_job_source(job.id, raw_job)

        # 8. Update Company job counter
        await self.company_repo.increment_job_count(company.id)

        logger.info(
            "job_normalized_and_saved",
            job_id=job.id,
            company=company.name,
            title=job.title,
            is_duplicate=is_duplicate,
            skills_count=len(skill_records),
        )

        return job, True

    async def _ensure_job_source(self, job_id: str, raw_job: RawJobData) -> None:
        """Create or update JobSource record tracking raw response."""
        existing = await self.source_repo.get_by_job_and_source(job_id, raw_job.source_type)
        if not existing:
            await self.source_repo.create(
                job_id=job_id,
                source_type=raw_job.source_type,
                source_url=raw_job.posting_url,
                source_job_id=raw_job.external_id,
                raw_data=raw_job.raw_data,
            )

    def _normalize_salary(
        self,
        min_val: int | None,
        max_val: int | None,
        period: str | None,
    ) -> tuple[int | None, int | None]:
        """Normalize hourly/monthly salary values to annual integer rates."""
        if not min_val and not max_val:
            return None, None

        multiplier = 1.0
        p_lower = (period or "yearly").lower()

        if "hour" in p_lower:
            multiplier = 2080.0  # 40 hrs/wk * 52 wks
        elif "month" in p_lower:
            multiplier = 12.0

        norm_min = int(min_val * multiplier) if min_val else None
        norm_max = int(max_val * multiplier) if max_val else None

        return norm_min, norm_max
