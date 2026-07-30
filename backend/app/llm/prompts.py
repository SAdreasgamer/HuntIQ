"""
HuntIQ — Prompt Template Library.

Centralized system prompts and prompt templates for all AI intelligence tasks:
- Match Explanation
- Cover Letter Generation
- Recruiter Message Generation
- Interview Preparation
- Company Intelligence Profiling
"""

from __future__ import annotations

# ==============================================================
# System Prompts
# ==============================================================

SYSTEM_PROMPT_MATCH_EXPLAINER = """You are HuntIQ's Principal Recruitment Analyst & AI Hiring Engine.
Your task is to analyze candidate fit against job requirements with extreme precision.
Evaluate technical alignment, experience level, domain overlap, and identify true skill gaps.
Be objective, constructive, and highly specific. Output valid JSON adhering to the target schema.
"""

SYSTEM_PROMPT_COVER_LETTER = """You are an elite Executive Resume Writer and Job Search Coach.
Your task is to generate compelling, tailored, non-generic cover letters that highlight high-impact achievements.
Avoid cliché corporate jargon (e.g. 'I am excited to apply', 'hardworking professional').
Focus on technical alignment, quantifiable outcomes, and strategic fit.
"""

SYSTEM_PROMPT_RECRUITER_MESSAGE = """You are a senior tech candidate writing direct outreach messages to engineering managers and technical recruiters on LinkedIn or email.
Keep messages concise (100-150 words), professional, confident, and focused on specific engineering value.
"""

SYSTEM_PROMPT_INTERVIEW_PREP = """You are a Principal Software Engineer and Technical Interviewer at a top tier tech company.
Generate tailored interview questions (technical, architectural, behavioral) and detailed sample answers based on a job description and candidate resume.
"""

SYSTEM_PROMPT_COMPANY_INTELLIGENCE = """You are an AI Competitive Intelligence Analyst specializing in corporate tech stacks, hiring velocity, engineering culture, and glassdoor insights.
Generate a structured company profile for candidates preparing for interviews.
"""


# ==============================================================
# Prompt Templates
# ==============================================================

def build_match_explanation_prompt(
    job_title: str,
    company_name: str,
    job_description: str,
    resume_summary: str,
    resume_skills: list[str],
    experience_years: float,
    rule_score: float,
    embedding_score: float,
) -> str:
    """Build prompt for AI Match Explanation."""
    skills_str = ", ".join(resume_skills) if resume_skills else "None listed"
    return f"""Analyze the candidate match for the following opportunity:

JOB OPPORTUNITY:
- Title: {job_title}
- Company: {company_name}
- Description:
{job_description[:2000]}

CANDIDATE PROFILE:
- Total Experience: {experience_years} years
- Summary: {resume_summary or 'N/A'}
- Skills: {skills_str}
- Preliminary Rule Match Score: {rule_score}/100
- Vector Embedding Similarity: {embedding_score}/100

Please provide a JSON object with:
- "summary": (2-3 sentences explaining match)
- "key_strengths": (list of top 3 matching strengths)
- "skill_gaps": (list of missing skills or domain gaps)
- "shortlist_probability": (float 0.0 - 1.0)
- "tailoring_tips": (list of 3 actionable resume/application adjustment tips)
"""


def build_cover_letter_prompt(
    job_title: str,
    company_name: str,
    job_description: str,
    candidate_name: str,
    resume_summary: str,
    matched_skills: list[str],
    work_experience_highlights: list[str],
    tone: str = "professional",
) -> str:
    """Build prompt for Cover Letter Generation."""
    skills_str = ", ".join(matched_skills) if matched_skills else "Software Engineering"
    exp_str = "\n".join(f"- {h}" for h in work_experience_highlights[:5])

    return f"""Write a compelling cover letter for the following job application:

CANDIDATE NAME: {candidate_name}
TARGET COMPANY: {company_name}
TARGET ROLE: {job_title}
TONE: {tone}

KEY MATCHED SKILLS: {skills_str}

CANDIDATE HIGHLIGHTS:
{exp_str}

JOB DESCRIPTION SUMMARY:
{job_description[:1500]}

INSTRUCTIONS:
- Create 3-4 structured paragraphs:
  1. Strong hook mentioning candidate background and direct value for {company_name}.
  2. Technical deep-dive demonstrating relevant experience with {skills_str}.
  3. Alignment with company mission and quantifiable achievements.
  4. Confident call to action.
- Do NOT use placehoder tags like [Insert Name]. Use provided candidate details.
"""


def build_recruiter_message_prompt(
    job_title: str,
    company_name: str,
    recruiter_name: str | None,
    candidate_name: str,
    key_skills: list[str],
    channel: str = "linkedin",
) -> str:
    """Build prompt for Recruiter Outreach Message."""
    recipient = recruiter_name or "Hiring Manager"
    skills_str = ", ".join(key_skills[:4])

    return f"""Draft a short, high-conversion outreach message:

RECIPIENT: {recipient}
COMPANY: {company_name}
ROLE: {job_title}
CANDIDATE NAME: {candidate_name}
CHANNEL: {channel} (Max 150 words)
KEY SKILLS: {skills_str}

Requirements:
- Professional, concise, direct.
- Highlight candidate's hands-on experience in {skills_str}.
- End with a low-friction call to action (e.g. 10-min intro call).
"""
