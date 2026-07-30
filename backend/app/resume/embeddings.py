"""
HuntIQ — Resume Embedding Service.

Generates dense vector embeddings for resume versions using sentence-transformers.
Stores vector embeddings in DB via ResumeEmbeddingRepository for semantic matching.
Includes fallback hash-based vector generator for environments without PyTorch/transformers.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.exceptions import EmbeddingError
from app.core.logging import get_logger
from app.models.resume import ResumeEmbedding, ResumeVersion
from app.repositories.resume import ResumeEmbeddingRepository
from app.resume.schemas import ParsedResumeData

logger = get_logger(__name__)

# Default model name & dimension constant
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_DIMENSIONS = 384


class ResumeEmbeddingService:
    """Service generating vector embeddings for resumes."""

    def __init__(self, model_name: str | None = None) -> None:
        """
        Initialize the embedding service.

        Args:
            model_name: HuggingFace model identifier (default: all-MiniLM-L6-v2).
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

                logger.info("loading_embedding_model", model=self.model_name)
                self._model = SentenceTransformer(self.model_name)
            except Exception as exc:
                logger.warning(
                    "sentence_transformers_unavailable_using_fallback",
                    model=self.model_name,
                    error=str(exc),
                )
                self._use_fallback = True
        return self._model

    def build_source_text(self, parsed_data: ParsedResumeData) -> str:
        """
        Construct normalized, dense text representation of resume for vector embedding.

        Combines summary, categorized skills, and work experience highlights.
        """
        parts: list[str] = []

        if parsed_data.summary:
            parts.append(f"Summary: {parsed_data.summary.strip()}")

        if parsed_data.skills:
            skills_str = ", ".join(parsed_data.skills)
            parts.append(f"Skills: {skills_str}")

        for exp in parsed_data.work_experience:
            bullets_str = " ".join(exp.bullet_points) if exp.bullet_points else ""
            parts.append(f"Role: {exp.title} at {exp.company}. {bullets_str}")

        for edu in parsed_data.education:
            parts.append(f"Education: {edu.degree or ''} in {edu.field_of_study or ''} from {edu.institution}")

        source_text = "\n".join(parts).strip()
        if not source_text and parsed_data.raw_text:
            source_text = parsed_data.raw_text[:2000]

        return source_text

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
                logger.warning("sentence_transformers_encode_failed", error=str(exc))

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

    async def create_or_update_embedding(
        self,
        session: AsyncSession,
        resume_version: ResumeVersion,
        parsed_data: ParsedResumeData,
    ) -> ResumeEmbedding:
        """
        Generate and persist embedding vector for a ResumeVersion in DB.

        Args:
            session: Async DB session.
            resume_version: Target ResumeVersion model.
            parsed_data: Structured resume schema.

        Returns:
            Persisted ResumeEmbedding ORM instance.
        """
        source_text = self.build_source_text(parsed_data)
        vector, text_hash = self.generate_embedding(source_text)

        repo = ResumeEmbeddingRepository(session)
        embedding_record = await repo.upsert(
            resume_version_id=resume_version.id,
            embedding=vector,
            model_name=self.model_name if not self._use_fallback else "fallback-hash-v1",
            dimensions=len(vector),
            source_text_hash=text_hash,
        )

        logger.info(
            "resume_embedding_saved",
            resume_version_id=resume_version.id,
            model=embedding_record.model_name,
            dimensions=len(vector),
        )
        return embedding_record

    @staticmethod
    def compute_cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """
        Compute cosine similarity between two vectors.

        Returns:
            Float value between 0.0 and 1.0.
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = math.sqrt(sum(a * a for a in vec1))
        norm_b = math.sqrt(sum(b * b for b in vec2))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        similarity = dot_product / (norm_a * norm_b)
        # Clamp to [0.0, 1.0] range
        return max(0.0, min(1.0, float(similarity)))
