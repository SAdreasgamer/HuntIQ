"""
LLM Integration subsystem.

Abstracts LLM providers (OpenRouter, Ollama, Mock) behind a common interface
and provides a resilient fallback chain with aggressive response caching,
structured JSON parsing, and AI Match Explanations.

Usage:
    from app.llm import LLMFallbackChain, LLMCacheService, MatchExplainerService

    explainer = MatchExplainerService()
    explanation, is_cached = await explainer.explain_job_match(session, job_id, resume_id)
"""

from app.llm.base import LLMProvider
from app.llm.cache import LLMCacheService
from app.llm.chain import LLMFallbackChain, MockLLMProvider
from app.llm.explainer import MatchExplainerService
from app.llm.prompts import (
    SYSTEM_PROMPT_COVER_LETTER,
    SYSTEM_PROMPT_INTERVIEW_PREP,
    SYSTEM_PROMPT_MATCH_EXPLAINER,
    SYSTEM_PROMPT_RECRUITER_MESSAGE,
    build_cover_letter_prompt,
    build_match_explanation_prompt,
    build_recruiter_message_prompt,
)
from app.llm.providers.ollama import OllamaLLMProvider
from app.llm.providers.openrouter import OpenRouterLLMProvider
from app.llm.schemas import (
    AIJobMatchExplanation,
    LLMRequest,
    LLMResponse,
    LLMTaskType,
)

__all__ = [
    # Base, Chain, Providers, Cache, Explainer
    "LLMProvider",
    "LLMFallbackChain",
    "MockLLMProvider",
    "OpenRouterLLMProvider",
    "OllamaLLMProvider",
    "LLMCacheService",
    "MatchExplainerService",
    # Schemas
    "LLMTaskType",
    "LLMRequest",
    "LLMResponse",
    "AIJobMatchExplanation",
    # Prompts
    "SYSTEM_PROMPT_MATCH_EXPLAINER",
    "SYSTEM_PROMPT_COVER_LETTER",
    "SYSTEM_PROMPT_RECRUITER_MESSAGE",
    "SYSTEM_PROMPT_INTERVIEW_PREP",
    "build_match_explanation_prompt",
    "build_cover_letter_prompt",
    "build_recruiter_message_prompt",
]
