"""
HuntIQ — Scraper Data Schemas.

Pydantic models for raw scraped data and normalized job output.
Every provider converts its raw response into a RawJobData instance,
which then gets normalized into the SQLAlchemy Job model.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class RawJobData(BaseModel):
    """
    Standardized raw job data output from any provider.

    Every provider implementation must convert its platform-specific
    response into this schema. The normalization service then maps
    this to the Job ORM model.
    """

    # Required fields
    title: str = Field(..., description="Job title")
    company_name: str = Field(..., description="Company name")
    source_type: str = Field(..., description="Provider identifier (linkedin, greenhouse, etc.)")

    # Location
    location: str | None = Field(default=None, description="Job location")
    is_remote: bool = Field(default=False, description="Whether the job is remote")
    country: str | None = Field(default=None, description="Country")

    # Description
    description: str | None = Field(default=None, description="Full job description")
    requirements: str | None = Field(default=None, description="Job requirements")
    responsibilities: str | None = Field(default=None, description="Job responsibilities")

    # Compensation
    salary_min: int | None = Field(default=None, description="Minimum salary")
    salary_max: int | None = Field(default=None, description="Maximum salary")
    salary_currency: str | None = Field(default=None, description="Currency code")
    salary_period: str | None = Field(default=None, description="yearly, monthly, hourly")

    # Experience
    experience_min: int | None = Field(default=None, description="Min years of experience")
    experience_max: int | None = Field(default=None, description="Max years of experience")
    seniority_level: str | None = Field(default=None, description="entry, mid, senior, lead")

    # Employment
    employment_type: str | None = Field(default=None, description="full-time, contract, etc.")

    # URLs
    posting_url: str | None = Field(default=None, description="Original posting URL")
    apply_url: str | None = Field(default=None, description="Direct apply URL")

    # Identifiers
    external_id: str | None = Field(default=None, description="Platform-specific job ID")

    # Skills / Tech
    skills: list[str] = Field(default_factory=list, description="Extracted skill names")
    tech_stack: list[str] = Field(default_factory=list, description="Extracted technologies")

    # Company metadata
    company_website: str | None = Field(default=None, description="Company website URL")
    company_logo_url: str | None = Field(default=None, description="Company logo URL")
    company_industry: str | None = Field(default=None, description="Company industry")
    company_size: str | None = Field(default=None, description="Employee count range")

    # Dates
    posted_at: datetime | None = Field(default=None, description="Original posting date")
    expires_at: datetime | None = Field(default=None, description="Posting expiry date")

    # Raw data preservation
    raw_data: dict | None = Field(default=None, description="Original platform response")

    model_config = {"extra": "ignore"}


class SearchInput(BaseModel):
    """Input parameters for a job search."""

    keywords: list[str] = Field(..., description="Search keywords")
    locations: list[str] = Field(default_factory=list, description="Target locations")
    excluded_keywords: list[str] = Field(default_factory=list, description="Keywords to exclude")
    max_results: int = Field(default=100, description="Max results to retrieve")


class ProviderResult(BaseModel):
    """Result from a single provider search run."""

    provider_name: str = Field(..., description="Provider identifier")
    jobs: list[RawJobData] = Field(default_factory=list, description="Scraped jobs")
    total_found: int = Field(default=0, description="Total results found by the provider")
    errors: list[str] = Field(default_factory=list, description="Non-fatal errors encountered")
    duration_seconds: float = Field(default=0.0, description="Search duration")

    @property
    def success_count(self) -> int:
        """Number of successfully scraped jobs."""
        return len(self.jobs)

    @property
    def has_errors(self) -> bool:
        """Whether any errors occurred."""
        return len(self.errors) > 0
