"""
Recruitment Intelligence subsystem.

Generates AI job intelligence artifacts:
- Tailored cover letters
- Recruiter outreach messages
- Technical & behavioral interview preparation kits
- Company tech stack & culture intelligence
"""

from app.intelligence.cover_letter import CoverLetterGeneratorService

__all__ = [
    "CoverLetterGeneratorService",
]
