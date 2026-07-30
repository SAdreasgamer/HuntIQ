"""
API middleware components.

This package contains FastAPI middleware for cross-cutting concerns:

- RequestIDMiddleware: Injects X-Request-ID into every request/response
- TimingMiddleware: Logs request execution time
- RateLimitMiddleware: Redis-backed rate limiting
- CORSMiddleware: Cross-Origin Resource Sharing configuration
"""
