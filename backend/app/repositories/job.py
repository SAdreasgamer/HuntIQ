"""
Job, JobSkill, JobSource, and JobEmbedding repositories.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.models.job import Job, JobEmbedding, JobSkill, JobSource
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    """Repository for Job model operations."""

    model = Job

    async def get_with_relations(self, job_id: str) -> Job | None:
        """Get a job with skills, sources, and company eagerly loaded."""
        stmt = (
            select(Job)
            .where(Job.id == job_id)
            .options(
                selectinload(Job.skills),
                selectinload(Job.sources),
                selectinload(Job.company),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_content_hash(self, content_hash: str) -> Job | None:
        """Find a job by its content hash (deduplication)."""
        return await self.get_by_field("content_hash", content_hash)

    async def get_by_external_id(self, external_id: str) -> Job | None:
        """Find a job by its external platform ID."""
        return await self.get_by_field("external_id", external_id)

    async def find_duplicates(
        self,
        company_id: str,
        title: str,
        posting_url: str | None = None,
    ) -> Sequence[Job]:
        """Find potential duplicate jobs by company + title + URL."""
        conditions = [
            Job.company_id == company_id,
            func.lower(Job.title) == title.lower(),
            Job.is_duplicate.is_(False),
        ]
        if posting_url:
            conditions_with_url = [*conditions, Job.posting_url == posting_url]
            stmt = select(Job).where(and_(*conditions_with_url))
            result = await self.session.execute(stmt)
            matches = result.scalars().all()
            if matches:
                return matches

        stmt = select(Job).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_active(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        min_score: float | None = None,
        is_remote: bool | None = None,
        location: str | None = None,
        company_id: str | None = None,
    ) -> Sequence[Job]:
        """List active (non-closed, non-duplicate) jobs with filters."""
        stmt = select(Job).where(
            Job.is_active.is_(True),
            Job.is_duplicate.is_(False),
        )
        if min_score is not None:
            stmt = stmt.where(Job.match_score >= min_score)
        if is_remote is not None:
            stmt = stmt.where(Job.is_remote == is_remote)
        if location:
            stmt = stmt.where(
                or_(
                    func.lower(Job.location).contains(location.lower()),
                    func.lower(Job.country).contains(location.lower()),
                )
            )
        if company_id:
            stmt = stmt.where(Job.company_id == company_id)

        stmt = stmt.order_by(Job.match_score.desc().nulls_last()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_top_matches(
        self,
        limit: int = 50,
        min_score: float = 0,
    ) -> Sequence[Job]:
        """Get top-scoring job matches."""
        stmt = (
            select(Job)
            .where(
                Job.is_active.is_(True),
                Job.is_duplicate.is_(False),
                Job.match_score.isnot(None),
                Job.match_score >= min_score,
            )
            .options(selectinload(Job.company), selectinload(Job.skills))
            .order_by(Job.match_score.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_recent(self, hours: int = 24, limit: int = 50) -> Sequence[Job]:
        """Get jobs found in the last N hours."""
        cutoff = datetime.now(timezone.utc).replace(
            hour=datetime.now(timezone.utc).hour - hours
            if datetime.now(timezone.utc).hour >= hours
            else 0
        )
        stmt = (
            select(Job)
            .where(Job.created_at >= cutoff, Job.is_duplicate.is_(False))
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_unscored(self, limit: int = 100) -> Sequence[Job]:
        """Get jobs that haven't been scored yet."""
        stmt = (
            select(Job)
            .where(
                Job.match_score.is_(None),
                Job.is_active.is_(True),
                Job.is_duplicate.is_(False),
            )
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_inactive(self, job_id: str) -> None:
        """Mark a job as inactive (closed/expired)."""
        await self.update(job_id, is_active=False)

    async def mark_duplicate(self, job_id: str, original_id: str) -> None:
        """Mark a job as a duplicate of another job."""
        await self.update(job_id, is_duplicate=True, duplicate_of_id=original_id)

    async def count_active(self) -> int:
        """Count active, non-duplicate jobs."""
        return await self.count(filters={"is_active": True, "is_duplicate": False})

    async def count_remote(self) -> int:
        """Count active remote jobs."""
        stmt = (
            select(func.count())
            .select_from(Job)
            .where(Job.is_active.is_(True), Job.is_remote.is_(True))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def search(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[Job]:
        """Full-text search across job title and description."""
        pattern = f"%{query.lower()}%"
        stmt = (
            select(Job)
            .where(
                Job.is_active.is_(True),
                or_(
                    func.lower(Job.title).like(pattern),
                    func.lower(Job.description).like(pattern),
                ),
            )
            .order_by(Job.match_score.desc().nulls_last())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class JobSkillRepository(BaseRepository[JobSkill]):
    """Repository for JobSkill model operations."""

    model = JobSkill

    async def get_by_job_id(self, job_id: str) -> Sequence[JobSkill]:
        """Get all skills for a job."""
        stmt = select(JobSkill).where(JobSkill.job_id == job_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_top_skills(self, limit: int = 30) -> list[tuple[str, int]]:
        """Get the most frequently requested skills across all jobs."""
        stmt = (
            select(JobSkill.skill_name, func.count(JobSkill.id).label("count"))
            .group_by(JobSkill.skill_name)
            .order_by(func.count(JobSkill.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]


class JobSourceRepository(BaseRepository[JobSource]):
    """Repository for JobSource model operations."""

    model = JobSource

    async def get_by_job_and_source(
        self,
        job_id: str,
        source_type: str,
    ) -> JobSource | None:
        """Get a source record for a specific job and provider."""
        stmt = select(JobSource).where(
            JobSource.job_id == job_id,
            JobSource.source_type == source_type,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def count_by_source(self) -> list[tuple[str, int]]:
        """Count jobs found per source provider."""
        stmt = (
            select(JobSource.source_type, func.count(JobSource.id).label("count"))
            .group_by(JobSource.source_type)
            .order_by(func.count(JobSource.id).desc())
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]


class JobEmbeddingRepository(BaseRepository[JobEmbedding]):
    """Repository for JobEmbedding model operations."""

    model = JobEmbedding

    async def get_by_job_id(self, job_id: str) -> JobEmbedding | None:
        """Get the embedding for a specific job."""
        return await self.get_by_field("job_id", job_id)

    async def upsert(self, job_id: str, **kwargs: object) -> JobEmbedding:
        """Create or update an embedding for a job."""
        existing = await self.get_by_job_id(job_id)
        if existing:
            for key, value in kwargs.items():
                setattr(existing, key, value)
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        return await self.create(job_id=job_id, **kwargs)
