"""
LLMCache repository.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, delete, select

from app.models.llm_cache import LLMCache
from app.repositories.base import BaseRepository


class LLMCacheRepository(BaseRepository[LLMCache]):
    """Repository for LLMCache model operations."""

    model = LLMCache

    async def get_cached(
        self,
        content_hash: str,
        task_type: str,
        resume_version_id: str | None = None,
    ) -> LLMCache | None:
        """
        Look up a cached LLM response.

        Args:
            content_hash: SHA-256 hash of the job/content.
            task_type: LLM task type identifier.
            resume_version_id: Resume version ID (None for resume-independent tasks).

        Returns:
            The cached entry if found and not expired, None otherwise.
        """
        conditions = [
            LLMCache.content_hash == content_hash,
            LLMCache.task_type == task_type,
        ]
        if resume_version_id:
            conditions.append(LLMCache.resume_version_id == resume_version_id)
        else:
            conditions.append(LLMCache.resume_version_id.is_(None))

        stmt = select(LLMCache).where(and_(*conditions))
        result = await self.session.execute(stmt)
        entry = result.scalars().first()

        if entry is None:
            return None

        # Check expiration
        if entry.expires_at and entry.expires_at < datetime.now(timezone.utc):
            await self.delete(entry.id)
            return None

        return entry

    async def store(
        self,
        content_hash: str,
        task_type: str,
        resume_version_id: str | None,
        provider: str,
        model: str,
        prompt_hash: str,
        response_text: str,
        response_structured: dict | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
        latency_ms: int | None = None,
        ttl_seconds: int = 604800,
    ) -> LLMCache:
        """
        Store an LLM response in the cache.

        Args:
            content_hash: SHA-256 hash of the content.
            task_type: LLM task type.
            resume_version_id: Resume version ID.
            provider: LLM provider used.
            model: LLM model used.
            prompt_hash: Hash of the prompt.
            response_text: Raw response text.
            response_structured: Parsed response data.
            prompt_tokens: Prompt token count.
            completion_tokens: Completion token count.
            total_tokens: Total token count.
            latency_ms: Response latency.
            ttl_seconds: Cache TTL (default 7 days).

        Returns:
            The created cache entry.
        """
        from datetime import timedelta

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

        # Delete existing entry if any (upsert)
        existing = await self.get_cached(content_hash, task_type, resume_version_id)
        if existing:
            await self.delete(existing.id)

        return await self.create(
            content_hash=content_hash,
            task_type=task_type,
            resume_version_id=resume_version_id,
            provider=provider,
            model=model,
            prompt_hash=prompt_hash,
            response_text=response_text,
            response_structured=response_structured,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            expires_at=expires_at,
        )

    async def clear_expired(self) -> int:
        """Delete all expired cache entries."""
        now = datetime.now(timezone.utc)
        stmt = delete(LLMCache).where(
            LLMCache.expires_at.isnot(None),
            LLMCache.expires_at < now,
        )
        result = await self.session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]

    async def clear_by_task_type(self, task_type: str) -> int:
        """Clear all cache entries for a specific task type."""
        stmt = delete(LLMCache).where(LLMCache.task_type == task_type)
        result = await self.session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]
