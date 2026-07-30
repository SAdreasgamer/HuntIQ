"""
Recruitment Intelligence subsystem.

Generates AI job intelligence artifacts:
- Tailored cover letters
- Recruiter outreach messages
- Technical & behavioral interview preparation kits
- Company tech stack & culture intelligence
"""

from app.intelligence.company import (
    CompanyIntelligenceProfile,
    CompanyIntelligenceService,
)
from app.intelligence.cover_letter import CoverLetterGeneratorService
from app.intelligence.interview_prep import (
    InterviewPrepKit,
    InterviewPrepService,
    InterviewQuestion,
)
from app.intelligence.recruiter_message import (
    RecruiterMessageGeneratorService,
    RecruiterOutreachMessage,
)

__all__ = [
    "CoverLetterGeneratorService",
    "RecruiterMessageGeneratorService",
    "RecruiterOutreachMessage",
    "InterviewPrepService",
    "InterviewPrepKit",
    "InterviewQuestion",
    "CompanyIntelligenceService",
    "CompanyIntelligenceProfile",
]
