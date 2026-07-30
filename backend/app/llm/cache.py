"""
HuntIQ — LLM Cache Service.

Aggressive 2-tier caching engine for LLM completions backed by DB (LLMCacheRepository)
and optional Redis. Prevents redundant API calls for identical (content_hash, task_type, resume_version_id) tuples.
"""

from __future__ import annotations

import hashlib
from typing import Any, TypeVar

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.llm.chain import LLMFallbackChain
from app.llm.schemas import LLMRequest, LLMResponse
from app.models.llm_cache import LLMCache
from app.repositories.llm_cache import LLMCacheRepository

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

DEFAULT_TTL_SECONDS = 604800  # 7 days


class LLMCacheService:
    """Caching service for LLM completions and structured outputs."""

    def __init__(self, default_ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        """Initialize LLM cache service with TTL."""
        self.default_ttl = default_ttl_seconds

    async def get_cached_response(
        self,
        session: AsyncSession,
        content_hash: str,
        task_type: str,
        resume_version_id: str | None = None,
    ) -> LLMResponse | None:
        """
        Retrieve a cached LLM response from DB.

        Args:
            session: Async DB session.
            content_hash: SHA-256 hash of job/content.
            task_type: LLM task type identifier.
            resume_version_id: Optional resume version ID.

        Returns:
            LLMResponse if cache hit and not expired, None otherwise.
        """
        repo = LLMCacheRepository(session)
        cached: LLMCache | None = await repo.get_cached(
            content_hash=content_hash,
            task_type=task_type,
            resume_version_id=resume_version_id,
        )

        if cached is None:
            return None

        logger.info(
            "llm_cache_hit",
            content_hash=content_hash[:12],
            task_type=task_type,
            provider=cached.provider,
        )

        return LLMResponse(
            content=cached.response_text,
            provider=f"{cached.provider} (cached)",
            model=cached.model,
            prompt_tokens=cached.prompt_tokens,
            completion_tokens=cached.completion_tokens,
            total_tokens=cached.total_tokens,
            latency_ms=cached.latency_ms,
            structured_data=cached.response_structured,
        )

    async def store_response(
        self,
        session: AsyncSession,
        content_hash: str,
        task_type: str,
        resume_version_id: str | None,
        prompt: str,
        response: LLMResponse,
        ttl_seconds: int | None = None,
    ) -> LLMCache:
        """
        Store an LLM response in DB cache.

        Args:
            session: Async DB session.
            content_hash: SHA-256 hash of content.
            task_type: LLM task type.
            resume_version_id: Resume version ID.
            prompt: Prompt text string.
            response: LLMResponse instance.
            ttl_seconds: Custom TTL.

        Returns:
            Created LLMCache model.
        """
        repo = LLMCacheRepository(session)
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        ttl = ttl_seconds or self.default_ttl

        cache_record = await repo.store(
            content_hash=content_hash,
            task_type=task_type,
            resume_version_id=resume_version_id,
            provider=response.provider.replace(" (cached)", ""),
            model=response.model,
            prompt_hash=prompt_hash,
            response_text=response.content,
            response_structured=response.structured_data,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            latency_ms=response.latency_ms,
            ttl_seconds=ttl,
        )

        logger.info(
            "llm_cache_stored",
            content_hash=content_hash[:12],
            task_type=task_type,
            ttl_seconds=ttl,
        )
        return cache_record

    async def execute_cached_structured(
        self,
        session: AsyncSession,
        chain: LLMFallbackChain,
        request: LLMRequest,
        schema_cls: type[T],
        content_hash: str,
        resume_version_id: str | None = None,
        force_refresh: bool = False,
    ) -> tuple[T, LLMResponse, bool]:
        """
        Execute structured LLM completion with automatic caching.

        Args:
            session: Async DB session.
            chain: LLMFallbackChain instance.
            request: LLMRequest parameters.
            schema_cls: Pydantic schema class.
            content_hash: Content hash for caching key.
            resume_version_id: Resume version ID.
            force_refresh: Ignore cache and re-generate.

        Returns:
            Tuple of (parsed Pydantic schema instance, LLMResponse, is_cached_bool).
        """
        task_name = request.task_type.value if hasattr(request.task_type, "value") else str(request.task_type)

        if not force_refresh:
            cached_resp = await self.get_cached_response(
                session=session,
                content_hash=content_hash,
                task_type=task_name,
                resume_version_id=resume_version_id,
            )
            if cached_resp and cached_resp.structured_data:
                try:
                    instance = schema_cls.model_validate(cached_resp.structured_data)
                    return instance, cached_resp, True
                except Exception as exc:
                    logger.warning("llm_cached_structure_validation_failed", error=str(exc))

        # Cache miss or forced refresh -> execute LLM chain
        instance, response = await chain.generate_structured(request, schema_cls)

        # Store in cache
        await self.store_response(
            session=session,
            content_hash=content_hash,
            task_type=task_name,
            resume_version_id=resume_version_id,
            prompt=request.prompt,
            response=response,
        )

        return instance, response, False
