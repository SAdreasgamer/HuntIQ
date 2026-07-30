"""
HuntIQ — LLM Fallback Chain & Mock Provider.

Orchestrates LLM providers in a prioritized fallback sequence.
If primary provider (e.g. OpenRouter) fails due to rate limits or API outage,
transparently falls back to secondary provider (e.g. Ollama) or Mock fallback.
"""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from app.core.exceptions import LLMError
from app.core.logging import get_logger
from app.llm.base import LLMProvider
from app.llm.schemas import LLMRequest, LLMResponse

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """Fallback mock LLM provider for offline testing and guaranteed responses."""

    provider_name = "mock"
    default_model = "mock-gpt-4o"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Return structured mock responses based on task type."""
        logger.info("mock_llm_generating", task_type=request.task_type)

        content = """{
  "summary": "Strong candidate match with 4+ years of relevant backend experience in Python and PostgreSQL.",
  "key_strengths": ["Strong Python & FastAPI expertise", "Distributed systems experience", "Cloud infrastructure familiarity"],
  "skill_gaps": ["Kubernetes administration"],
  "shortlist_probability": 0.88,
  "tailoring_tips": ["Highlight AWS deployment experience in summary", "Add Kubernetes lab projects if available"]
}"""

        if "cover letter" in request.prompt.lower():
            content = f"Dear Hiring Team,\n\nI am writing to express my strong interest in the role. With my background in backend engineering and cloud architecture, I am confident in my ability to add immediate value to your team.\n\nSincerely,\nCandidate"

        return LLMResponse(
            content=content,
            provider=self.provider_name,
            model=self.default_model,
            prompt_tokens=100,
            completion_tokens=150,
            total_tokens=250,
            latency_ms=15,
        )


class LLMFallbackChain:
    """Orchestrates multiple LLM providers in prioritized fallback order."""

    def __init__(self, providers: list[LLMProvider] | None = None) -> None:
        """
        Initialize the fallback chain.

        Args:
            providers: Ordered list of LLMProvider instances.
        """
        self.providers = providers or [MockLLMProvider()]

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate completion using the first available provider in the chain.

        Args:
            request: LLMRequest parameters.

        Returns:
            LLMResponse object.
        """
        errors: list[str] = []

        for provider in self.providers:
            try:
                logger.info(
                    "llm_chain_attempt",
                    provider=provider.provider_name,
                    task_type=request.task_type,
                )
                return await provider.generate(request)
            except Exception as exc:
                error_msg = f"Provider {provider.provider_name} failed: {exc}"
                errors.append(error_msg)
                logger.warning(
                    "llm_chain_provider_failed",
                    provider=provider.provider_name,
                    error=str(exc),
                )

        raise LLMError(
            provider="chain",
            message=f"All LLM providers in chain failed: {'; '.join(errors)}",
            details={"errors": errors},
        )

    async def generate_structured(
        self,
        request: LLMRequest,
        schema_cls: type[T],
    ) -> tuple[T, LLMResponse]:
        """
        Generate structured output using the first available provider in chain.

        Args:
            request: LLMRequest parameters.
            schema_cls: Target Pydantic schema class.

        Returns:
            Tuple of (parsed instance, raw LLMResponse).
        """
        errors: list[str] = []

        for provider in self.providers:
            try:
                logger.info(
                    "llm_chain_structured_attempt",
                    provider=provider.provider_name,
                    schema=schema_cls.__name__,
                )
                return await provider.generate_structured(request, schema_cls)
            except Exception as exc:
                error_msg = f"Provider {provider.provider_name} structured failed: {exc}"
                errors.append(error_msg)
                logger.warning(
                    "llm_chain_provider_structured_failed",
                    provider=provider.provider_name,
                    error=str(exc),
                )

        raise LLMError(
            provider="chain",
            message=f"All LLM providers in fallback chain failed for structured output: {'; '.join(errors)}",
            details={"errors": errors},
        )
