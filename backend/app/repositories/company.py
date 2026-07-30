"""
Company repository.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select

from app.models.company import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    """Repository for Company model operations."""

    model = Company

    async def get_by_normalized_name(self, name: str) -> Company | None:
        """Get a company by its normalized (lowercased, stripped) name."""
        normalized = name.strip().lower()
        return await self.get_by_field("normalized_name", normalized)

    async def get_or_create(self, name: str, **kwargs: str | None) -> tuple[Company, bool]:
        """
        Get an existing company or create a new one.

        Args:
            name: Company name.
            **kwargs: Additional fields for creation.

        Returns:
            Tuple of (company, created) where created is True if new.
        """
        normalized = name.strip().lower()
        existing = await self.get_by_normalized_name(normalized)
        if existing:
            return existing, False
        company = await self.create(
            name=name.strip(),
            normalized_name=normalized,
            **kwargs,
        )
        return company, True

    async def get_favorites(self) -> Sequence[Company]:
        """Get all favorite companies."""
        stmt = select(Company).where(Company.is_favorite.is_(True)).order_by(Company.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_blacklisted(self) -> Sequence[Company]:
        """Get all blacklisted companies."""
        stmt = select(Company).where(Company.is_blacklisted.is_(True))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_by_name(self, query: str, limit: int = 20) -> Sequence[Company]:
        """Search companies by name (case-insensitive partial match)."""
        pattern = f"%{query.lower()}%"
        stmt = (
            select(Company)
            .where(Company.normalized_name.like(pattern))
            .order_by(Company.name)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_top_by_jobs(self, limit: int = 20) -> Sequence[Company]:
        """Get companies with the most job listings."""
        stmt = (
            select(Company)
            .where(Company.total_jobs_found > 0)
            .order_by(Company.total_jobs_found.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def increment_job_count(self, company_id: str) -> None:
        """Increment the total_jobs_found counter for a company."""
        company = await self.get_by_id_or_raise(company_id)
        company.total_jobs_found += 1
        await self.session.flush()

    async def update_average_match_score(self, company_id: str) -> None:
        """Recalculate and update the average match score for a company."""
        from app.models.job import Job

        stmt = (
            select(func.avg(Job.match_score))
            .where(Job.company_id == company_id)
            .where(Job.match_score.isnot(None))
        )
        result = await self.session.execute(stmt)
        avg_score = result.scalar()
        if avg_score is not None:
            company = await self.get_by_id_or_raise(company_id)
            company.average_match_score = float(avg_score)
            await self.session.flush()
