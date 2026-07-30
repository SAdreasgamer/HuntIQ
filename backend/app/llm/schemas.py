"""
HuntIQ — LLM Integration Schemas.

Pydantic schemas for LLM prompts, structured outputs, and provider responses.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LLMTaskType(str, Enum):
    """Supported LLM task categories."""

    MATCH_EXPLANATION = "match_explanation"
    COVER_LETTER = "cover_letter"
    RECRUITER_MESSAGE = "recruiter_message"
    INTERVIEW_PREP = "interview_prep"
    COMPANY_INTELLIGENCE = "company_intelligence"
    SKILL_EXTRACTION = "skill_extraction"


class LLMRequest(BaseModel):
    """Generic LLM request parameters."""

    prompt: str = Field(..., description="Main prompt text")
    system_prompt: str | None = Field(default=None, description="System instructions")
    task_type: LLMTaskType = Field(default=LLMTaskType.MATCH_EXPLANATION, description="Task category")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=1000, gt=0, description="Max completion tokens")
    response_format: str | None = Field(default=None, description="Optional 'json_object' mode")


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider."""

    content: str = Field(..., description="Generated text content")
    provider: str = Field(..., description="Provider name (openrouter, ollama, mock)")
    model: str = Field(..., description="Model name used")
    prompt_tokens: int | None = Field(default=None, description="Input token count")
    completion_tokens: int | None = Field(default=None, description="Output token count")
    total_tokens: int | None = Field(default=None, description="Total tokens used")
    latency_ms: int | None = Field(default=None, description="Request duration in ms")
    structured_data: dict[str, Any] | None = Field(default=None, description="Parsed JSON response if applicable")

    model_config = {"extra": "ignore"}


class AIJobMatchExplanation(BaseModel):
    """Structured output schema for AI Job Match Explanations."""

    summary: str = Field(..., description="Executive summary of why candidate matches job")
    key_strengths: list[str] = Field(default_factory=list, description="Top matching strengths")
    skill_gaps: list[str] = Field(default_factory=list, description="Missing skills or experience gaps")
    shortlist_probability: float = Field(..., description="Estimated shortlist probability (0.0 - 1.0)")
    tailoring_tips: list[str] = Field(default_factory=list, description="Actionable tips to tailor application")
