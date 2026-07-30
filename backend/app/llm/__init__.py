"""
LLM Integration subsystem.

Abstracts LLM providers (OpenRouter, Ollama, Mock) behind a common interface
and provides a resilient fallback chain with structured JSON parsing.

Usage:
    from app.llm import LLMFallbackChain, OpenRouterLLMProvider, OllamaLLMProvider, MockLLMProvider

    chain = LLMFallbackChain([
        OpenRouterLLMProvider(),
        OllamaLLMProvider(model="qwen"),
        MockLLMProvider(),
    ])
    explanation, response = await chain.generate_structured(request, AIJobMatchExplanation)
"""

from app.llm.base import LLMProvider
from app.llm.chain import LLMFallbackChain, MockLLMProvider
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
    # Base & Chain & Providers
    "LLMProvider",
    "LLMFallbackChain",
    "MockLLMProvider",
    "OpenRouterLLMProvider",
    "OllamaLLMProvider",
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
