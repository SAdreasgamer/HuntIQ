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
from app.llm.schemas import LLMRequest, LLMResponse, LLMTaskType

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """Fallback mock LLM provider for offline testing and guaranteed responses."""

    provider_name = "mock"
    default_model = "mock-gpt-4o"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Return structured mock responses based on task type."""
        task_str = str(request.task_type).lower()
        logger.info("mock_llm_generating", task_type=request.task_type)

        content = """{
  "summary": "Strong candidate match with 4+ years of relevant backend experience in Python and PostgreSQL.",
  "key_strengths": ["Strong Python & FastAPI expertise", "Distributed systems experience", "Cloud infrastructure familiarity"],
  "skill_gaps": ["Kubernetes administration"],
  "shortlist_probability": 0.88,
  "tailoring_tips": ["Highlight AWS deployment experience in summary", "Add Kubernetes lab projects if available"]
}"""

        if "company" in task_str or LLMTaskType.COMPANY_INTELLIGENCE in task_str:
            content = """{
  "company_name": "Target Company",
  "industry": "Enterprise Software",
  "estimated_engineering_size": "250-500",
  "known_tech_stack": ["Python", "FastAPI", "Go", "PostgreSQL", "AWS"],
  "engineering_culture_highlights": [
    "Strong emphasis on automated CI/CD pipelines and unit test coverage",
    "Blameless post-mortem culture with high engineering autonomy",
    "Flexible remote-first hybrid work environment"
  ],
  "interview_process_summary": "4-stage pipeline: Recruiter screen (30m), Technical coding round (60m), System architecture interview (60m), and Culture fit with VP of Engineering (45m).",
  "hiring_velocity_rating": "high",
  "pros": ["High compensation competitive with Big Tech", "Modern tech stack", "Fast career progression"],
  "cons": ["On-call rotation every 6 weeks", "Rapidly evolving roadmap requirements"],
  "recommended_questions_to_ask_interviewer": [
    "How does the engineering team balance technical debt resolution against feature delivery?",
    "What are the key metrics used to evaluate success for a Senior Engineer in their first 90 days?",
    "What does your deployment frequency look like across production microservices?"
  ]
}"""

        elif "interview" in task_str or LLMTaskType.INTERVIEW_PREP in task_str:
            content = """{
  "job_title": "Target Role",
  "company_name": "Target Company",
  "technical_questions": [
    {
      "question": "How do you handle distributed transactions and lock contention across microservices?",
      "category": "technical",
      "difficulty": "hard",
      "key_points_to_mention": ["Two-phase commit", "Saga pattern", "Eventual consistency"],
      "sample_star_answer": "In my previous system, I implemented the Saga pattern using Kafka event streams to guarantee eventual consistency..."
    }
  ],
  "behavioral_questions": [
    {
      "question": "Describe a situation where you resolved a critical production incident under high pressure.",
      "category": "behavioral",
      "difficulty": "medium",
      "key_points_to_mention": ["Root cause analysis", "Post-mortem documentation", "Blameless culture"],
      "sample_star_answer": "When database connection pools were exhausted during peak traffic..."
    }
  ],
  "system_design_questions": [
    {
      "question": "Design a globally distributed rate limiter capable of handling 1M RPS with sub-10ms latency.",
      "category": "system_design",
      "difficulty": "hard",
      "key_points_to_mention": ["Token bucket algorithm", "Redis cluster caching", "Slide window counters"],
      "sample_star_answer": "I would architecture a multi-region Redis cluster using local memory sliding windows..."
    }
  ],
  "top_preparation_tips": [
    "Review core concurrency primitives and memory layout",
    "Prepare 3 STAR stories highlighting high scale architecture",
    "Familiarize yourself with target company's open source stack"
  ]
}"""

        elif "cover" in request.prompt.lower() or "cover_letter" in task_str:
            content = "Dear Hiring Team,\n\nI am writing to express my strong interest in the role. With my background in backend engineering and cloud architecture, I am confident in my ability to add immediate value to your team.\n\nSincerely,\nCandidate"

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
