"""
HuntIQ — Abstract LLM Provider Base Class.

Every LLM provider (OpenRouter, Ollama, OpenAI, Mock) inherits from LLMProvider.
Enforces common interface for async generation and structured Pydantic output parsing.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from app.core.exceptions import LLMError, LLMResponseError
from app.core.logging import get_logger
from app.llm.schemas import LLMRequest, LLMResponse

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    provider_name: str = ""
    default_model: str = ""

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text completion from prompt.

        Args:
            request: Standardized LLMRequest.

        Returns:
            LLMResponse object.
        """

    async def generate_structured(
        self,
        request: LLMRequest,
        schema_cls: type[T],
    ) -> tuple[T, LLMResponse]:
        """
        Generate completion and parse response into a Pydantic schema class.

        Args:
            request: LLMRequest parameters.
            schema_cls: Pydantic BaseModel subclass.

        Returns:
            Tuple of (parsed Pydantic instance, raw LLMResponse).
        """
        # Ensure system prompt instructs JSON response
        system_instruction = (
            (request.system_prompt or "")
            + "\nRespond strictly in valid JSON matching the schema."
        ).strip()

        request.system_prompt = system_instruction
        request.response_format = "json_object"

        response = await self.generate(request)

        # Parse JSON
        content = response.content.strip()
        # Clean markdown codeblocks if wrapped in ```json ... ```
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        try:
            data_dict = json.loads(content)
            instance = schema_cls.model_validate(data_dict)
            response.structured_data = data_dict
            return instance, response
        except json.JSONDecodeError as exc:
            logger.error("llm_json_decode_failed", provider=self.provider_name, content=content[:200])
            raise LLMResponseError(
                provider=self.provider_name,
                message=f"LLM returned invalid JSON: {exc}",
            ) from exc
        except Exception as exc:
            logger.error("llm_schema_validation_failed", provider=self.provider_name, error=str(exc))
            raise LLMResponseError(
                provider=self.provider_name,
                message=f"LLM JSON failed schema validation for {schema_cls.__name__}: {exc}",
            ) from exc
