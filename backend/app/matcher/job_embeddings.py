"""
HuntIQ — Job Embedding Service.

Generates dense 384-dimensional vector embeddings for normalized job listings using sentence-transformers.
Stores vector embeddings in DB via JobEmbeddingRepository for semantic similarity scoring.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.exceptions import EmbeddingError
from app.core.logging import get_logger
from app.models.job import Job, JobEmbedding
from app.repositories.job import JobEmbeddingRepository, JobRepository

logger = get_logger(__name__)

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_DIMENSIONS = 384


class JobEmbeddingService:
    """Service generating vector embeddings for job listings."""

    def __init__(self, model_name: str | None = None) -> None:
        """
        Initialize the job embedding service.

        Args:
            model_name: HuggingFace model identifier.
        """
        settings = get_settings()
        self.model_name = model_name or settings.matching.embedding_model or DEFAULT_MODEL_NAME
        self.dimensions = settings.matching.embedding_dimensions or DEFAULT_DIMENSIONS
        self._model: Any = None
        self._use_fallback = False

    def _get_model(self) -> Any:
        """Lazy load SentenceTransformer model with fallback."""
        if self._model is None and not self._use_fallback:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("loading_job_embedding_model", model=self.model_name)
                self._model = SentenceTransformer(self.model_name)
            except Exception as exc:
                logger.warning(
                    "sentence_transformers_unavailable_using_fallback",
                    model=self.model_name,
                    error=str(exc),
                )
                self._use_fallback = True
        return self._model

    def build_source_text(self, job: Job) -> str:
        """
        Construct normalized, dense text representation of job for vector embedding.

        Combines role title, company, location, seniority, tech stack, and description.
        Safe against un-eager-loaded relationships in async SQLAlchemy.
        """
        parts: list[str] = [
            f"Title: {job.title}",
        ]

        # Safely inspect company attribute state
        state = inspect(job)
        if state and "company" not in state.unloaded and job.company:
            parts.append(f"Company: {job.company.name}")

        if job.location:
            remote_str = " (Remote)" if job.is_remote else ""
            parts.append(f"Location: {job.location}{remote_str}")

        if job.seniority_level:
            parts.append(f"Seniority: {job.seniority_level}")

        if job.tech_stack:
            skills_str = ", ".join(job.tech_stack) if isinstance(job.tech_stack, list) else str(job.tech_stack)
            parts.append(f"Tech Stack: {skills_str}")

        if job.description:
            parts.append(f"Description: {job.description[:1500].strip()}")

        return "\n".join(parts).strip()

    def generate_embedding(self, text: str) -> tuple[list[float], str]:
        """
        Generate embedding vector for text string.

        Returns:
            Tuple of (embedding_vector, text_sha256_hash).
        """
        if not text:
            raise EmbeddingError(message="Cannot generate embedding for empty text")

        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        model = self._get_model()

        if model is not None:
            try:
                vector = model.encode(text, convert_to_numpy=True).tolist()
                return [float(val) for val in vector], text_hash
            except Exception as exc:
                logger.warning("sentence_transformers_job_encode_failed", error=str(exc))

        # Fallback deterministic vector generator
        vector = self._generate_fallback_vector(text)
        return vector, text_hash

    def _generate_fallback_vector(self, text: str) -> list[float]:
        """Generate deterministic normalized vector from text hash for testing/fallback."""
        vec = []
        words = text.lower().split()
        for i in range(self.dimensions):
            val = sum(hash(w + str(i)) % 100 for w in words) if words else hash(str(i)) % 100
            vec.append(float(val))

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    async def generate_for_job(self, session: AsyncSession, job: Job) -> JobEmbedding:
        """
        Generate and persist embedding vector for a single Job record in DB.

        Args:
            session: Async DB session.
            job: Target Job model.

        Returns:
            Persisted JobEmbedding ORM instance.
        """
        source_text = self.build_source_text(job)
        vector, text_hash = self.generate_embedding(source_text)

        repo = JobEmbeddingRepository(session)
        embedding_record = await repo.upsert(
            job_id=job.id,
            embedding=vector,
            model_name=self.model_name if not self._use_fallback else "fallback-hash-v1",
            dimensions=len(vector),
            source_text_hash=text_hash,
        )

        logger.info(
            "job_embedding_saved",
            job_id=job.id,
            model=embedding_record.model_name,
            dimensions=len(vector),
        )
        return embedding_record

    async def batch_generate_unembedded_jobs(self, session: AsyncSession, limit: int = 50) -> int:
        """
        Batch generate embeddings for all active jobs missing vector embeddings.

        Args:
            session: Async DB session.
            limit: Max jobs to process in one batch.

        Returns:
            Number of jobs successfully embedded.
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # Find jobs missing embeddings
        stmt = (
            select(Job)
            .outerjoin(JobEmbedding)
            .where(
                Job.is_active.is_(True),
                Job.is_duplicate.is_(False),
                JobEmbedding.id.is_(None),
            )
            .options(selectinload(Job.company))
            .limit(limit)
        )

        result = await session.execute(stmt)
        jobs_to_embed = list(result.scalars().all())

        count = 0
        for job in jobs_to_embed:
            try:
                await self.generate_for_job(session, job)
                count += 1
            except Exception as exc:
                logger.error("batch_job_embedding_failed", job_id=job.id, error=str(exc))

        await session.flush()
        logger.info("batch_job_embeddings_completed", count=count, limit=limit)
        return count
