"""
HuntIQ — Rule-Based Matching Engine.

Evaluates job listings against user resumes and preferences across 7 weighted dimensions:
1. Skills match (25%)
2. Role title match (20%)
3. Experience match (15%)
4. Tech stack match (15%)
5. Keyword match (10%)
6. Location & remote match (10%)
7. Company preference match (5%)

Produces a composite rule_score (0-100) along with detailed dimension breakdown and missing skills.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from app.config.settings import get_settings
from app.core.logging import get_logger
from app.models.company import Company
from app.models.job import Job
from app.models.user import UserPreference
from app.resume.schemas import ParsedResumeData

logger = get_logger(__name__)


class RuleMatchResult(BaseModel):
    """Detailed output of rule-based evaluation."""

    rule_score: float = Field(..., description="Weighted composite score (0-100)")
    skills_score: float = Field(default=0.0, description="Skills dimension score (0-100)")
    role_score: float = Field(default=0.0, description="Role title dimension score (0-100)")
    experience_score: float = Field(default=0.0, description="Experience dimension score (0-100)")
    tech_stack_score: float = Field(default=0.0, description="Tech stack dimension score (0-100)")
    keyword_score: float = Field(default=0.0, description="Keyword dimension score (0-100)")
    location_score: float = Field(default=0.0, description="Location dimension score (0-100)")
    company_score: float = Field(default=0.0, description="Company preference score (0-100)")
    matched_skills: list[str] = Field(default_factory=list, description="Skills present in resume")
    missing_skills: list[str] = Field(default_factory=list, description="Skills required by job but missing in resume")
    is_blacklisted: bool = Field(default=False, description="Whether company or job is blacklisted")


class RuleMatcher:
    """7-dimension weighted rule matching engine."""

    def __init__(self) -> None:
        """Initialize matcher with weights from application settings."""
        settings = get_settings()
        self.cfg = settings.matching

    def evaluate(
        self,
        job: Job,
        resume_data: ParsedResumeData,
        user_pref: UserPreference | None = None,
        company: Company | None = None,
    ) -> RuleMatchResult:
        """
        Evaluate a Job against ParsedResumeData and UserPreference.

        Args:
            job: Target Job model.
            resume_data: Parsed structured resume.
            user_pref: Optional UserPreference model.
            company: Optional Company model.

        Returns:
            RuleMatchResult with composite score and sub-scores.
        """
        # Check blacklist first
        comp_obj = company or getattr(job, "company", None)
        if comp_obj and getattr(comp_obj, "is_blacklisted", False):
            return RuleMatchResult(rule_score=0.0, is_blacklisted=True)

        user_skills = {s.lower().strip() for s in resume_data.skills}

        # 1. Skills Score (25%)
        job_skills = set()
        if job.skills:
            job_skills.update(s.skill_name.lower().strip() for s in job.skills)
        if job.tech_stack and isinstance(job.tech_stack, list):
            job_skills.update(str(s).lower().strip() for s in job.tech_stack)

        matched_skills = sorted(user_skills.intersection(job_skills))
        missing_skills = sorted(job_skills.difference(user_skills))

        if job_skills:
            skills_score = (len(matched_skills) / len(job_skills)) * 100.0
        else:
            skills_score = 70.0  # neutral fallback if job skills not explicit

        # 2. Role Title Score (20%)
        role_score = self._evaluate_role(job.title, user_pref, resume_data)

        # 3. Experience Score (15%)
        exp_score = self._evaluate_experience(
            user_years=resume_data.total_experience_years,
            job_min=job.experience_min,
            job_max=job.experience_max,
        )

        # 4. Tech Stack Score (15%)
        tech_score = self._evaluate_tech_stack(job.tech_stack, user_skills)

        # 5. Keyword Score (10%)
        keyword_score = self._evaluate_keywords(job, user_pref)

        # 6. Location & Remote Score (10%)
        location_score = self._evaluate_location(job, user_pref)

        # 7. Company Score (5%)
        company_score = self._evaluate_company(comp_obj, user_pref)

        # Compute weighted composite score
        composite = (
            (skills_score * self.cfg.weight_skills)
            + (role_score * self.cfg.weight_role)
            + (exp_score * self.cfg.weight_experience)
            + (tech_score * self.cfg.weight_tech_stack)
            + (keyword_score * self.cfg.weight_keywords)
            + (location_score * self.cfg.weight_location)
            + (company_score * self.cfg.weight_company_pref)
        )

        final_score = round(max(0.0, min(100.0, composite)), 2)

        return RuleMatchResult(
            rule_score=final_score,
            skills_score=round(skills_score, 2),
            role_score=round(role_score, 2),
            experience_score=round(exp_score, 2),
            tech_stack_score=round(tech_score, 2),
            keyword_score=round(keyword_score, 2),
            location_score=round(location_score, 2),
            company_score=round(company_score, 2),
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            is_blacklisted=False,
        )

    def _evaluate_role(
        self,
        job_title: str,
        user_pref: UserPreference | None,
        resume_data: ParsedResumeData,
    ) -> float:
        """Evaluate role title match against user preferred roles and resume experience."""
        title_lower = job_title.lower()
        preferred_roles: list[str] = []

        if user_pref and user_pref.preferred_roles and isinstance(user_pref.preferred_roles, list):
            preferred_roles.extend(str(r).lower() for r in user_pref.preferred_roles)

        for exp in resume_data.work_experience:
            if exp.title:
                preferred_roles.append(exp.title.lower())

        if not preferred_roles:
            preferred_roles = ["backend engineer", "software engineer", "developer"]

        score = 0.0
        for pref in preferred_roles:
            pref_words = set(pref.split())
            title_words = set(title_lower.split())
            common = pref_words.intersection(title_words)
            if common:
                ratio = (len(common) / max(len(pref_words), 1)) * 100.0
                score = max(score, ratio)

        return score if score > 0 else 30.0

    def _evaluate_experience(
        self,
        user_years: float,
        job_min: int | None,
        job_max: int | None,
    ) -> float:
        """Evaluate user experience against job minimum and maximum requirements."""
        if job_min is None and job_max is None:
            return 100.0

        min_req = float(job_min or 0)
        max_req = float(job_max or 30)

        if user_years >= min_req and user_years <= max_req + 2:
            return 100.0
        elif user_years < min_req:
            diff = min_req - user_years
            return max(0.0, 100.0 - (diff * 25.0))
        else:  # Overqualified
            diff = user_years - max_req
            return max(50.0, 100.0 - (diff * 10.0))

    def _evaluate_tech_stack(self, job_tech_stack: Any, user_skills: set[str]) -> float:
        """Evaluate tech stack list against user skills."""
        if not job_tech_stack:
            return 80.0

        techs = []
        if isinstance(job_tech_stack, list):
            techs = [str(t).lower().strip() for t in job_tech_stack]
        elif isinstance(job_tech_stack, str):
            techs = [t.lower().strip() for t in job_tech_stack.split(",")]

        if not techs:
            return 80.0

        matched = [t for t in techs if t in user_skills]
        return (len(matched) / len(techs)) * 100.0

    def _evaluate_keywords(self, job: Job, user_pref: UserPreference | None) -> float:
        """Evaluate excluded and blacklisted keywords against job description."""
        text = f"{job.title} {job.description or ''}".lower()

        # Check blacklisted keywords from preference
        if user_pref and user_pref.blacklisted_keywords and isinstance(user_pref.blacklisted_keywords, list):
            for kw in user_pref.blacklisted_keywords:
                if str(kw).lower().strip() in text:
                    return 0.0

        return 85.0

    def _evaluate_location(self, job: Job, user_pref: UserPreference | None) -> float:
        """Evaluate job location and remote flag against user preferred locations."""
        if job.is_remote:
            return 100.0

        if not user_pref or not user_pref.preferred_locations or not isinstance(user_pref.preferred_locations, list):
            return 80.0

        pref_locs = [str(l).lower().strip() for l in user_pref.preferred_locations]
        job_loc = (job.location or "").lower()

        for loc in pref_locs:
            if loc in job_loc or loc in (job.country or "").lower():
                return 100.0

        return 40.0

    def _evaluate_company(self, company: Company | None, user_pref: UserPreference | None) -> float:
        """Evaluate company preferences (favorite, blacklisted, preferred)."""
        if not company:
            return 70.0

        if company.is_favorite:
            return 100.0
        if company.is_blacklisted:
            return 0.0

        if user_pref and user_pref.preferred_companies and isinstance(user_pref.preferred_companies, list):
            norm_comp = company.normalized_name
            for pref in user_pref.preferred_companies:
                if str(pref).lower().strip() in norm_comp:
                    return 90.0

        return 70.0
