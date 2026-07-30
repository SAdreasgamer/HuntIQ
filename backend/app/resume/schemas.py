"""
HuntIQ — Resume Schemas.

Pydantic models representing the structured JSON output of parsed resumes.
Parsed ONCE from PDF, stored in database, and consumed by downstream matching engine.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    """Extracted resume contact information."""

    full_name: str | None = Field(default=None, description="Full name")
    email: str | None = Field(default=None, description="Email address")
    phone: str | None = Field(default=None, description="Phone number")
    linkedin_url: str | None = Field(default=None, description="LinkedIn profile URL")
    github_url: str | None = Field(default=None, description="GitHub profile URL")
    portfolio_url: str | None = Field(default=None, description="Personal website or portfolio URL")
    location: str | None = Field(default=None, description="City, state, or country")


class WorkExperience(BaseModel):
    """Individual work experience entry."""

    company: str = Field(..., description="Company or organization name")
    title: str = Field(..., description="Job title / role")
    location: str | None = Field(default=None, description="Job location")
    start_date: str | None = Field(default=None, description="Start date string (e.g. 'Jan 2021')")
    end_date: str | None = Field(default=None, description="End date string (e.g. 'Present')")
    is_current: bool = Field(default=False, description="Whether currently working here")
    description: str | None = Field(default=None, description="Summary or raw description")
    bullet_points: list[str] = Field(default_factory=list, description="Bullet points / achievements")
    technologies: list[str] = Field(default_factory=list, description="Technologies used in this role")


class Education(BaseModel):
    """Education entry."""

    institution: str = Field(..., description="University, college, or school name")
    degree: str | None = Field(default=None, description="Degree earned (e.g., 'B.Tech', 'M.S.')")
    field_of_study: str | None = Field(default=None, description="Field of study / major (e.g., 'Computer Science')")
    graduation_year: int | str | None = Field(default=None, description="Graduation year or date range")
    gpa: str | None = Field(default=None, description="GPA or percentage if available")


class Project(BaseModel):
    """Personal or professional project entry."""

    title: str = Field(..., description="Project title")
    description: str | None = Field(default=None, description="Project description")
    technologies: list[str] = Field(default_factory=list, description="Technologies used")
    url: str | None = Field(default=None, description="Project URL or repo link")


class Certification(BaseModel):
    """Certification entry."""

    name: str = Field(..., description="Certification name")
    issuer: str | None = Field(default=None, description="Issuing organization")
    date_issued: str | None = Field(default=None, description="Date issued")


class SkillCategory(BaseModel):
    """Categorized skill set."""

    category: str = Field(..., description="Category name (e.g., 'Languages', 'Frameworks')")
    skills: list[str] = Field(default_factory=list, description="Skill names in this category")


class ParsedResumeData(BaseModel):
    """
    Complete structured output of a parsed resume.

    This single object contains all extracted entities from the PDF.
    Downstream processes (rule matcher, embedding generator, LLM) consume this directly.
    """

    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: str | None = Field(default=None, description="Professional summary / objective")
    total_experience_years: float = Field(default=0.0, description="Estimated total years of experience")
    skills: list[str] = Field(default_factory=list, description="Flat list of all unique skills")
    categorized_skills: list[SkillCategory] = Field(default_factory=list, description="Skills grouped by category")
    work_experience: list[WorkExperience] = Field(default_factory=list, description="Work experience history")
    education: list[Education] = Field(default_factory=list, description="Education background")
    projects: list[Project] = Field(default_factory=list, description="Personal or professional projects")
    certifications: list[Certification] = Field(default_factory=list, description="Certifications and licenses")
    raw_text: str = Field(default="", description="Full raw extracted text from PDF")

    model_config = {"extra": "ignore"}
