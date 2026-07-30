"""
Resume processing pipeline.

Parses PDF resumes into structured JSON models, manages versioning,
and computes resume vector embeddings for matching.

Usage:
    from app.resume import ResumeParser, ParsedResumeData

    parser = ResumeParser()
    resume_data = parser.parse("path/to/resume.pdf")
"""

from app.resume.parser import ResumeParser
from app.resume.schemas import (
    Certification,
    ContactInfo,
    Education,
    ParsedResumeData,
    Project,
    SkillCategory,
    WorkExperience,
)

__all__ = [
    "ResumeParser",
    "ParsedResumeData",
    "ContactInfo",
    "WorkExperience",
    "Education",
    "Project",
    "Certification",
    "SkillCategory",
]
