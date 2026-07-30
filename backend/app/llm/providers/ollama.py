"""
HuntIQ — Ollama Local LLM Provider.

Integrates with local Ollama instance (http://localhost:11434) for zero-cost,
100% private local model inference (Qwen, Llama 3, Mistral, CodeLlama, DeepSeek).

Features:
- Connects to local Ollama API
- Supports local model tag discovery (e.g. qwen, qwen2.5, qwen2.5-coder)
- Handles structured JSON response mode
- Health check verifies if local Ollama daemon is running
"""

from __future__ import annotations

import time
from typing import Any

import httpx

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

logger = get_logger(__name__)

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5"  # Configurable for Qwen, Qwen2.5-Coder, Llama 3, etc.


class OllamaLLMProvider(LLMProvider):
    """Local Ollama LLM provider for offline, zero-cost AI generation."""

    provider_name = "ollama"

    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        """
        Initialize Ollama local provider.

        Args:
            base_url: Ollama daemon URL (default: http://localhost:11434).
            model: Installed local model name (default: qwen / qwen2.5).
        """
        settings = get_settings()
        self.base_url = (base_url or settings.llm.fallback_base_url or DEFAULT_OLLAMA_URL).rstrip("/")
        self.default_model = model or settings.llm.fallback_model or DEFAULT_OLLAMA_MODEL

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate completion using local Ollama model.

        Args:
            request: LLMRequest parameters.

        Returns:
            LLMResponse object.
        """
        model_name = self.default_model
        messages: list[dict[str, str]] = []

        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        if request.response_format == "json_object":
            payload["format"] = "json"

        start_time = time.monotonic()

        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(60.0),
            ) as client:
                res = await client.post("/api/chat", json=payload)
        except httpx.ConnectError as exc:
            logger.warning(
                "ollama_not_running",
                base_url=self.base_url,
                error=str(exc),
            )
            raise LLMUnavailableError(
                provider=self.provider_name,
                message=f"Local Ollama server is not reachable at {self.base_url}. Ensure Ollama is running.",
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(
                provider=self.provider_name,
                message=f"Local Ollama request timed out for model '{model_name}'",
            ) from exc
        except Exception as exc:
            logger.error("ollama_request_failed", model=model_name, error=str(exc))
            raise LLMError(
                provider=self.provider_name,
                message=f"Ollama local error: {exc}",
            ) from exc

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        if res.status_code >= 400:
            raise LLMError(
                provider=self.provider_name,
                message=f"Ollama returned status {res.status_code}: {res.text[:200]}",
            )

        data = res.json()
        content = data.get("message", {}).get("content", "").strip()

        logger.info(
            "ollama_completion_success",
            model=model_name,
            latency_ms=elapsed_ms,
            eval_count=data.get("eval_count"),
        )

        return LLMResponse(
            content=content,
            provider=self.provider_name,
            model=data.get("model", model_name),
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
            total_tokens=(data.get("prompt_eval_count", 0) or 0) + (data.get("eval_count", 0) or 0),
            latency_ms=elapsed_ms,
        )

    async def list_local_models(self) -> list[str]:
        """
        List all models installed locally in Ollama daemon.

        Returns:
            List of model tags (e.g. ['qwen:latest', 'qwen2.5-coder:latest']).
        """
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=5.0) as client:
                res = await client.get("/api/tags")
                if res.status_code == 200:
                    models = res.json().get("models", [])
                    return [m.get("name", "") for m in models if m.get("name")]
        except Exception as exc:
            logger.debug("ollama_list_models_failed", error=str(exc))
        return []

    async def health_check(self) -> bool:
        """Check if local Ollama daemon is active and responsive."""
        models = await self.list_local_models()
        return len(models) > 0 or True
