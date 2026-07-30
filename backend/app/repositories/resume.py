"""
ResumeVersion, ResumeSkill, and ResumeEmbedding repositories.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.resume import ResumeEmbedding, ResumeSkill, ResumeVersion
from app.repositories.base import BaseRepository


class ResumeVersionRepository(BaseRepository[ResumeVersion]):
    """Repository for ResumeVersion model operations."""

    model = ResumeVersion

    async def get_by_user_id(self, user_id: str) -> Sequence[ResumeVersion]:
        """Get all resume versions for a user."""
        stmt = (
            select(ResumeVersion)
            .where(ResumeVersion.user_id == user_id)
            .options(selectinload(ResumeVersion.skills))
            .order_by(ResumeVersion.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_primary(self, user_id: str) -> ResumeVersion | None:
        """Get the primary resume version for a user."""
        stmt = select(ResumeVersion).where(
            ResumeVersion.user_id == user_id,
            ResumeVersion.is_primary.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_active(self, user_id: str) -> Sequence[ResumeVersion]:
        """Get all active resume versions for a user."""
        stmt = (
            select(ResumeVersion)
            .where(
                ResumeVersion.user_id == user_id,
                ResumeVersion.is_active.is_(True),
            )
            .order_by(ResumeVersion.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_file_hash(self, user_id: str, file_hash: str) -> ResumeVersion | None:
        """Check if a resume with this file hash already exists for the user."""
        stmt = select(ResumeVersion).where(
            ResumeVersion.user_id == user_id,
            ResumeVersion.file_hash == file_hash,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def set_primary(self, user_id: str, resume_id: str) -> None:
        """Set a resume as the primary version (unsets others)."""
        # Unset all primary flags for this user
        await self.bulk_update(
            filters={"user_id": user_id},
            values={"is_primary": False},
        )
        # Set the specified resume as primary
        await self.update(resume_id, is_primary=True)

    async def get_with_embedding(self, resume_id: str) -> ResumeVersion | None:
        """Get a resume version with its embedding eagerly loaded."""
        stmt = (
            select(ResumeVersion)
            .where(ResumeVersion.id == resume_id)
            .options(
                selectinload(ResumeVersion.skills),
                selectinload(ResumeVersion.embedding),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()


class ResumeSkillRepository(BaseRepository[ResumeSkill]):
    """Repository for ResumeSkill model operations."""

    model = ResumeSkill

    async def get_by_resume_id(self, resume_version_id: str) -> Sequence[ResumeSkill]:
        """Get all skills for a resume version."""
        stmt = select(ResumeSkill).where(
            ResumeSkill.resume_version_id == resume_version_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_skill_names(self, resume_version_id: str) -> list[str]:
        """Get just the skill names for a resume version."""
        stmt = select(ResumeSkill.skill_name).where(
            ResumeSkill.resume_version_id == resume_version_id
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]


class ResumeEmbeddingRepository(BaseRepository[ResumeEmbedding]):
    """Repository for ResumeEmbedding model operations."""

    model = ResumeEmbedding

    async def get_by_resume_id(self, resume_version_id: str) -> ResumeEmbedding | None:
        """Get the embedding for a specific resume version."""
        return await self.get_by_field("resume_version_id", resume_version_id)

    async def upsert(self, resume_version_id: str, **kwargs: object) -> ResumeEmbedding:
        """Create or update an embedding for a resume version."""
        existing = await self.get_by_resume_id(resume_version_id)
        if existing:
            for key, value in kwargs.items():
                setattr(existing, key, value)
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        return await self.create(resume_version_id=resume_version_id, **kwargs)
