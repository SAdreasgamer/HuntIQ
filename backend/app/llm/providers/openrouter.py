"""
HuntIQ — OpenRouter LLM Provider.

Integrates with OpenRouter API (https://openrouter.ai/api/v1) giving access
to 100+ AI models including free models (DeepSeek R1, Llama 3, Qwen, Mistral).

Handles authentication, rate limiting, retries, and token accounting.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config.settings import get_settings
from app.core.exceptions import (
    LLMError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from app.core.logging import get_logger
from app.llm.base import LLMProvider
from app.llm.schemas import LLMRequest, LLMResponse
from app.utils.rate_limiter import AsyncRateLimiter

logger = get_logger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "meta-llama/llama-3.1-8b-instruct:free"


class OpenRouterLLMProvider(LLMProvider):
    """OpenRouter LLM Provider with retry, rate limiting, and fallback model support."""

    provider_name = "openrouter"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        """Initialize OpenRouter provider with API credentials and default model."""
        settings = get_settings()
        key_val = api_key or (settings.llm.api_key.get_secret_value() if settings.llm.api_key else "")
        self.api_key = key_val
        self.default_model = model or settings.llm.model or DEFAULT_OPENROUTER_MODEL
        self.rate_limiter = AsyncRateLimiter(max_requests=20, window_seconds=60.0)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text completion via OpenRouter chat API.

        Args:
            request: LLMRequest parameters.

        Returns:
            LLMResponse object.
        """
        if not self.api_key or "your_" in self.api_key:
            raise LLMError(
                provider=self.provider_name,
                message="OpenRouter API key is not configured in settings",
            )

        model_name = self.default_model
        messages: list[dict[str, str]] = []

        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        if request.response_format == "json_object":
            payload["response_format"] = {"type": "json_object"}

        start_time = time.monotonic()

        await self.rate_limiter.acquire()

        try:
            async with httpx.AsyncClient(
                base_url=OPENROUTER_BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/SAdreasgamer/HuntIQ",
                    "X-Title": "HuntIQ Platform",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(45.0),
            ) as client:
                response = await self._send_request(client, payload)
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(
                "openrouter_request_failed",
                model=model_name,
                latency_ms=elapsed_ms,
                error=str(exc),
            )
            raise

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        # Extract content & usage
        try:
            choices = response.get("choices", [])
            if not choices:
                raise LLMResponseError(
                    provider=self.provider_name,
                    message="OpenRouter returned empty choices list",
                )

            content = choices[0].get("message", {}).get("content", "").strip()
            usage = response.get("usage", {})

            logger.info(
                "openrouter_completion_success",
                model=model_name,
                latency_ms=elapsed_ms,
                total_tokens=usage.get("total_tokens"),
            )

            return LLMResponse(
                content=content,
                provider=self.provider_name,
                model=response.get("model", model_name),
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
                latency_ms=elapsed_ms,
            )
        except (KeyError, IndexError) as exc:
            raise LLMResponseError(
                provider=self.provider_name,
                message=f"Failed to parse OpenRouter response: {exc}",
            ) from exc

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, LLMUnavailableError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        reraise=True,
    )
    async def _send_request(self, client: httpx.AsyncClient, payload: dict[str, Any]) -> dict[str, Any]:
        """Send HTTP POST request with tenacity retry handling."""
        try:
            res = await client.post("/chat/completions", json=payload)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(
                provider=self.provider_name,
                message="OpenRouter API request timed out after 45 seconds",
            ) from exc
        except httpx.TransportError as exc:
            logger.warning("openrouter_transport_error", error=str(exc))
            raise

        if res.status_code == 429:
            raise LLMRateLimitError(
                provider=self.provider_name,
                message="OpenRouter rate limit exceeded",
            )

        if res.status_code >= 500:
            raise LLMUnavailableError(
                provider=self.provider_name,
                message=f"OpenRouter server error {res.status_code}: {res.text[:200]}",
            )

        if res.status_code >= 400:
            raise LLMError(
                provider=self.provider_name,
                message=f"OpenRouter error {res.status_code}: {res.text[:300]}",
            )

        return res.json()
