"""
Matching engine subsystem.

Calculates match scores between user resumes and job listings using:
1. Rule-based weighted scoring (skills, role, experience, location, tech stack, keywords, company)
2. Semantic vector embeddings & cosine similarity (sentence-transformers)
3. LLM quality gate & deep analysis

Usage:
    from app.matcher import MatchingEngine, RuleMatcher, JobEmbeddingService

    engine = MatchingEngine()
    result = await engine.match_job(session, job_id, resume_version_id, user_id)
"""

from app.matcher.composite_matcher import CompositeMatchResult, MatchingEngine
from app.matcher.job_embeddings import JobEmbeddingService
from app.matcher.rule_matcher import RuleMatcher, RuleMatchResult

__all__ = [
    "JobEmbeddingService",
    "RuleMatcher",
    "RuleMatchResult",
    "MatchingEngine",
    "CompositeMatchResult",
]
