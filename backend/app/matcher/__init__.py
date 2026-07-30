"""
Matching engine subsystem.

Calculates match scores between user resumes and job listings using:
1. Rule-based weighted scoring (skills, role, experience, location, tech stack)
2. Semantic vector embeddings & cosine similarity (sentence-transformers)
3. LLM quality gate & deep analysis

Usage:
    from app.matcher import JobEmbeddingService

    service = JobEmbeddingService()
    await service.generate_for_job(session, job)
"""

from app.matcher.job_embeddings import JobEmbeddingService

__all__ = [
    "JobEmbeddingService",
]
