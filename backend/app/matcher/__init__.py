"""
Matching engine subsystem.

Calculates match scores between user resumes and job listings using:
1. Rule-based weighted scoring (skills, role, experience, location, tech stack, keywords, company)
2. Semantic vector embeddings & cosine similarity (sentence-transformers)
3. LLM quality gate & deep analysis

Usage:
    from app.matcher import RuleMatcher, JobEmbeddingService

    rule_matcher = RuleMatcher()
    result = rule_matcher.evaluate(job, resume_data, user_pref)
"""

from app.matcher.job_embeddings import JobEmbeddingService
from app.matcher.rule_matcher import RuleMatcher, RuleMatchResult

__all__ = [
    "JobEmbeddingService",
    "RuleMatcher",
    "RuleMatchResult",
]
