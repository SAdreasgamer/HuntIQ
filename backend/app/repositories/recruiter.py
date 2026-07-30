"""
Recruiter repository.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.recruiter import Recruiter
from app.repositories.base import BaseRepository


class RecruiterRepository(BaseRepository[Recruiter]):
    """Repository for Recruiter model operations."""

    model = Recruiter

    async def get_by_company(self, company_id: str) -> Sequence[Recruiter]:
        """Get all recruiters for a company."""
        stmt = (
            select(Recruiter)
            .where(Recruiter.company_id == company_id)
            .order_by(Recruiter.name)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_email(self, email: str) -> Recruiter | None:
        """Find a recruiter by email."""
        return await self.get_by_field("email", email)

    async def get_with_company(self, recruiter_id: str) -> Recruiter | None:
        """Get a recruiter with their company eagerly loaded."""
        stmt = (
            select(Recruiter)
            .where(Recruiter.id == recruiter_id)
            .options(selectinload(Recruiter.company))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def search(self, query: str, limit: int = 20) -> Sequence[Recruiter]:
        """Search recruiters by name or email."""
        from sqlalchemy import func, or_

        pattern = f"%{query.lower()}%"
        stmt = (
            select(Recruiter)
            .where(
                or_(
                    func.lower(Recruiter.name).like(pattern),
                    func.lower(Recruiter.email).like(pattern),
                )
            )
            .options(selectinload(Recruiter.company))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
