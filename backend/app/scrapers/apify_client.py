"""
HuntIQ — Apify API Client.

Manages all HTTP communication with the Apify platform.
Handles actor runs, dataset retrieval, rate limiting, retries,
and maps Apify errors to HuntIQ exceptions.

Architecture:
    ApifyClient is a low-level HTTP client. It does NOT know about
    job schemas or providers. Providers call this client to run
    actors and retrieve raw results.

Usage:
    from app.scrapers.apify_client import ApifyClient

    async with ApifyClient() as client:
        run = await client.run_actor(
            actor_id="apify/web-scraper",
            input_data={"startUrls": [...]},
        )
        items = await client.get_dataset_items(run["defaultDatasetId"])
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config.settings import get_settings
from app.core.exceptions import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.core.logging import get_logger
from app.utils.rate_limiter import AsyncRateLimiter

logger = get_logger(__name__)

# Apify API status codes
_STATUS_READY = "READY"
_STATUS_RUNNING = "RUNNING"
_STATUS_SUCCEEDED = "SUCCEEDED"
_STATUS_FAILED = "FAILED"
_STATUS_TIMED_OUT = "TIMED-OUT"
_STATUS_ABORTED = "ABORTED"

# Terminal statuses (run is done)
_TERMINAL_STATUSES = frozenset({_STATUS_SUCCEEDED, _STATUS_FAILED, _STATUS_TIMED_OUT, _STATUS_ABORTED})


class ApifyClient:
    """
    Async HTTP client for the Apify API.

    Handles authentication, rate limiting, retries with exponential
    backoff, actor lifecycle management, and dataset retrieval.
    """

    def __init__(self) -> None:
        """Initialize the client with settings from the configuration."""
        settings = get_settings()
        self._settings = settings.apify
        self._base_url = self._settings.base_url.rstrip("/")
        self._token = self._settings.token.get_secret_value()
        self._timeout = self._settings.default_timeout
        self._max_retries = self._settings.max_retries
        self._memory_mbytes = self._settings.memory_mbytes

        # Rate limiter: 30 requests per minute (Apify default)
        self._rate_limiter = AsyncRateLimiter(max_requests=30, window_seconds=60.0)

        # HTTP client (created on __aenter__)
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> ApifyClient:
        """Create the HTTP client on context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(
                connect=10.0,
                read=60.0,
                write=30.0,
                pool=10.0,
            ),
        )
        return self

    async def __aexit__(self, *args: object) -> None:
        """Close the HTTP client on context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client, raising if not initialized."""
        if self._client is None:
            msg = "ApifyClient must be used as an async context manager"
            raise RuntimeError(msg)
        return self._client

    # ==========================================================
    # Actor Management
    # ==========================================================

    async def run_actor(
        self,
        actor_id: str,
        input_data: dict[str, Any],
        *,
        memory_mbytes: int | None = None,
        timeout_secs: int | None = None,
        wait_for_finish: bool = True,
        build: str | None = None,
    ) -> dict[str, Any]:
        """
        Run an Apify actor and optionally wait for completion.

        Args:
            actor_id: Actor ID or username/actor-name.
            input_data: Actor input configuration.
            memory_mbytes: Memory allocation (overrides default).
            timeout_secs: Timeout for the run (overrides default).
            wait_for_finish: Whether to poll until the run completes.
            build: Specific build tag to use.

        Returns:
            Actor run metadata dict.

        Raises:
            ProviderAuthenticationError: If the API token is invalid.
            ProviderRateLimitError: If the rate limit is exceeded.
            ProviderTimeoutError: If the actor run times out.
            ProviderError: For any other Apify API errors.
        """
        memory = memory_mbytes or self._memory_mbytes
        timeout = timeout_secs or self._timeout

        params: dict[str, Any] = {
            "memory": memory,
            "timeout": timeout,
        }
        if build:
            params["build"] = build

        logger.info(
            "apify_actor_starting",
            actor_id=actor_id,
            memory_mbytes=memory,
            timeout_secs=timeout,
        )

        run_data = await self._request(
            "POST",
            f"/acts/{actor_id}/runs",
            json=input_data,
            params=params,
        )

        run_id = run_data["data"]["id"]
        logger.info("apify_actor_started", actor_id=actor_id, run_id=run_id)

        if wait_for_finish:
            run_data = await self._wait_for_run(
                actor_id=actor_id,
                run_id=run_id,
                timeout_secs=timeout,
            )

        return run_data["data"]

    async def _wait_for_run(
        self,
        actor_id: str,
        run_id: str,
        timeout_secs: int,
        poll_interval: float = 5.0,
    ) -> dict[str, Any]:
        """
        Poll an actor run until it reaches a terminal status.

        Args:
            actor_id: Actor ID (for logging).
            run_id: Run ID to poll.
            timeout_secs: Maximum wait time.
            poll_interval: Seconds between polls.

        Returns:
            Final run metadata.

        Raises:
            ProviderTimeoutError: If the run doesn't complete in time.
            ProviderError: If the run fails.
        """
        elapsed = 0.0

        while elapsed < timeout_secs:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            run_data = await self._request("GET", f"/actor-runs/{run_id}")
            status = run_data["data"]["status"]

            logger.debug(
                "apify_run_polling",
                run_id=run_id,
                status=status,
                elapsed_secs=elapsed,
            )

            if status in _TERMINAL_STATUSES:
                if status == _STATUS_SUCCEEDED:
                    logger.info(
                        "apify_actor_succeeded",
                        actor_id=actor_id,
                        run_id=run_id,
                        elapsed_secs=elapsed,
                    )
                    return run_data

                if status == _STATUS_TIMED_OUT:
                    raise ProviderTimeoutError(
                        provider="apify",
                        message=f"Actor {actor_id} timed out after {timeout_secs}s",
                    )

                error_msg = run_data["data"].get("statusMessage", "Unknown error")
                raise ProviderError(
                    provider="apify",
                    message=f"Actor {actor_id} failed with status {status}: {error_msg}",
                    details={"run_id": run_id, "status": status},
                )

        raise ProviderTimeoutError(
            provider="apify",
            message=f"Polling timeout: actor {actor_id} did not complete in {timeout_secs}s",
        )

    # ==========================================================
    # Dataset Retrieval
    # ==========================================================

    async def get_dataset_items(
        self,
        dataset_id: str,
        *,
        limit: int | None = None,
        offset: int = 0,
        fields: list[str] | None = None,
        clean: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Retrieve items from an Apify dataset.

        Args:
            dataset_id: The dataset ID to retrieve items from.
            limit: Maximum number of items to retrieve.
            offset: Number of items to skip.
            fields: Specific fields to retrieve (None = all).
            clean: Whether to return only non-empty items.

        Returns:
            List of dataset item dicts.
        """
        params: dict[str, Any] = {
            "clean": str(clean).lower(),
            "offset": offset,
        }
        if limit:
            params["limit"] = limit
        if fields:
            params["fields"] = ",".join(fields)

        response = await self._request(
            "GET",
            f"/datasets/{dataset_id}/items",
            params=params,
        )

        # The items endpoint returns a list directly, not wrapped in "data"
        if isinstance(response, list):
            items = response
        else:
            items = response.get("data", response)

        logger.info(
            "apify_dataset_retrieved",
            dataset_id=dataset_id,
            item_count=len(items),
        )
        return items

    # ==========================================================
    # Key-Value Store
    # ==========================================================

    async def get_key_value_record(
        self,
        store_id: str,
        key: str,
    ) -> dict[str, Any] | None:
        """
        Get a record from a key-value store.

        Args:
            store_id: The key-value store ID.
            key: The record key.

        Returns:
            The record data, or None if not found.
        """
        try:
            return await self._request("GET", f"/key-value-stores/{store_id}/records/{key}")
        except ProviderError:
            return None

    # ==========================================================
    # Run Management
    # ==========================================================

    async def abort_run(self, run_id: str) -> dict[str, Any]:
        """Abort a running actor."""
        return await self._request("POST", f"/actor-runs/{run_id}/abort")

    async def get_run(self, run_id: str) -> dict[str, Any]:
        """Get run metadata."""
        result = await self._request("GET", f"/actor-runs/{run_id}")
        return result["data"]

    async def get_run_log(self, run_id: str) -> str:
        """Get run log output."""
        response = await self.client.get(f"/actor-runs/{run_id}/log")
        response.raise_for_status()
        return response.text

    # ==========================================================
    # Internal HTTP Layer
    # ==========================================================

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, ProviderUnavailableError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """
        Make an authenticated HTTP request to the Apify API.

        Includes rate limiting, retry with exponential backoff,
        and error mapping to HuntIQ exceptions.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: API path (appended to base URL).
            json: JSON request body.
            params: Query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            ProviderAuthenticationError: On 401/403 responses.
            ProviderRateLimitError: On 429 responses.
            ProviderUnavailableError: On 5xx responses (retryable).
            ProviderTimeoutError: On request timeout.
            ProviderError: On any other HTTP error.
        """
        await self._rate_limiter.acquire()

        try:
            response = await self.client.request(
                method,
                path,
                json=json,
                params=params,
            )
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                provider="apify",
                message=f"Request timeout: {method} {path}",
            ) from exc
        except httpx.TransportError as exc:
            logger.warning(
                "apify_transport_error",
                method=method,
                path=path,
                error=str(exc),
            )
            raise

        # Map HTTP status codes to exceptions
        if response.status_code == 401 or response.status_code == 403:
            raise ProviderAuthenticationError(
                provider="apify",
                message="Invalid or expired API token",
            )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise ProviderRateLimitError(
                provider="apify",
                retry_after=int(retry_after) if retry_after else None,
            )

        if response.status_code >= 500:
            raise ProviderUnavailableError(
                provider="apify",
                message=f"Server error {response.status_code}: {response.text[:200]}",
            )

        if response.status_code >= 400:
            raise ProviderError(
                provider="apify",
                message=f"API error {response.status_code}: {response.text[:500]}",
                details={"status_code": response.status_code},
            )

        # Parse response
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text

    # ==========================================================
    # Health Check
    # ==========================================================

    async def health_check(self) -> bool:
        """
        Verify the Apify API connection and token validity.

        Returns:
            True if the connection is healthy.
        """
        try:
            result = await self._request("GET", "/users/me")
            username = result.get("data", {}).get("username", "unknown")
            logger.info("apify_health_ok", username=username)
            return True
        except (ProviderError, RetryError):
            logger.error("apify_health_failed")
            return False
