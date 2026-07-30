"""
HuntIQ — LLM Cache Repository.

Data access layer for LLMCache ORM model.
Supports cache lookup by (content_hash, task_type, resume_version_id),
storing cache hits with TTL, and cleanup of expired entries.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, select

from app.models.llm_cache import LLMCache
from app.repositories.base import BaseRepository


class LLMCacheRepository(BaseRepository[LLMCache]):
    """Repository managing cached LLM completions."""

    model = LLMCache

    async def get_cached(
        self,
        content_hash: str,
        task_type: str,
        resume_version_id: str | None = None,
    ) -> LLMCache | None:
        """
        Retrieve a non-expired cached LLM response.

        Args:
            content_hash: SHA-256 content hash.
            task_type: LLM task type name.
            resume_version_id: Optional resume version ID.

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

        # Check expiration (safely handling naive/aware datetimes)
        if entry.expires_at:
            exp_at = entry.expires_at
            if exp_at.tzinfo is None:
                exp_at = exp_at.replace(tzinfo=timezone.utc)
            if exp_at < datetime.now(timezone.utc):
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
        Store a new LLM completion response in the cache.

        Args:
            content_hash: SHA-256 hash of prompt/content.
            task_type: Task category identifier.
            resume_version_id: FK to ResumeVersion if applicable.
            provider: LLM provider name.
            model: Model identifier.
            prompt_hash: SHA-256 hash of the full prompt string.
            response_text: Raw LLM text completion.
            response_structured: Parsed JSON dictionary if applicable.
            prompt_tokens: Token count for prompt.
            completion_tokens: Token count for completion.
            total_tokens: Total token count.
            latency_ms: Request latency in ms.
            ttl_seconds: Cache TTL in seconds (default: 7 days).

        Returns:
            The created LLMCache entry.
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)

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
            created_at=now,
            expires_at=expires_at,
        )

    async def purge_expired(self) -> int:
        """
        Delete all expired cache entries.

        Returns:
            Count of deleted records.
        """
        now = datetime.now(timezone.utc)
        stmt = select(LLMCache).where(LLMCache.expires_at < now)
        result = await self.session.execute(stmt)
        expired_entries = list(result.scalars().all())

        for entry in expired_entries:
            await self.session.delete(entry)

        await self.session.flush()
        return len(expired_entries)
