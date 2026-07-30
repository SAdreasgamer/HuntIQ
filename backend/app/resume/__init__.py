"""
Resume processing pipeline.

Parses PDF resumes into structured JSON models, manages versioning,
stores files, and computes resume vector embeddings for matching.

Usage:
    from app.resume import ResumeParser, ResumeStorageService

    parser = ResumeParser()
    storage = ResumeStorageService()
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
from app.resume.storage import ResumeStorageService

__all__ = [
    "ResumeParser",
    "ParsedResumeData",
    "ContactInfo",
    "WorkExperience",
    "Education",
    "Project",
    "Certification",
    "SkillCategory",
    "ResumeStorageService",
]
