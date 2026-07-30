"""
HuntIQ — Async Rate Limiter.

Token-bucket rate limiter for controlling API request rates.
Used by the Apify client and LLM providers.
"""

from __future__ import annotations

import asyncio
import time


class AsyncRateLimiter:
    """
    Async token-bucket rate limiter.

    Limits operations to a maximum number per time window.
    Callers await `acquire()` before making requests.

    Usage:
        limiter = AsyncRateLimiter(max_requests=20, window_seconds=60)
        async with limiter:
            await make_api_call()
    """

    def __init__(self, max_requests: int, window_seconds: float = 60.0) -> None:
        """
        Initialize the rate limiter.

        Args:
            max_requests: Maximum number of requests per window.
            window_seconds: Time window in seconds.
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._tokens = float(max_requests)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Acquire a token, waiting if necessary.

        Blocks until a token is available.
        """
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return

            # Calculate wait time for next token
            wait_time = self.window_seconds / self.max_requests
            await asyncio.sleep(wait_time)

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        refill = elapsed * (self.max_requests / self.window_seconds)
        self._tokens = min(self._tokens + refill, float(self.max_requests))
        self._last_refill = now

    async def __aenter__(self) -> AsyncRateLimiter:
        """Acquire a token on context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, *args: object) -> None:
        """No cleanup needed on exit."""
