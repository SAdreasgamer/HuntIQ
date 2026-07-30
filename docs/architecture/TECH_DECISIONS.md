# HuntIQ — Technology Decisions

> Rationale behind every major technology and architectural choice.

---

## 1. Backend Framework: FastAPI

| Factor | Decision |
|---|---|
| **Choice** | FastAPI |
| **Alternatives Considered** | Django REST Framework, Flask, Litestar |
| **Rationale** | Native async support, Pydantic integration, automatic OpenAPI docs, high performance, first-class dependency injection, production-proven |
| **Trade-off** | Less opinionated than Django — requires explicit architecture decisions (which we prefer for this system) |

---

## 2. ORM: SQLAlchemy 2.0

| Factor | Decision |
|---|---|
| **Choice** | SQLAlchemy 2.0 with async support |
| **Alternatives Considered** | Tortoise ORM, SQLModel, raw asyncpg |
| **Rationale** | Industry standard, supports both sync and async, excellent PostgreSQL + SQLite support, mature migration tooling (Alembic), full control over query generation |
| **Key Pattern** | Repository pattern on top of SQLAlchemy for testability and abstraction |

---

## 3. Database: PostgreSQL (prod) + SQLite (dev)

| Factor | Decision |
|---|---|
| **Choice** | Dual database support |
| **Rationale** | SQLite for zero-config local development, PostgreSQL for production reliability, JSON column support in both, SQLAlchemy abstracts differences |
| **Key Decision** | Store structured resume/job JSON in native JSON columns rather than separate normalized tables — enables flexible schema evolution without migrations |
| **Embedding Storage** | Store as JSON arrays in database columns. For production scale, can migrate to pgvector later |

---

## 4. Task Queue: Celery + Redis

| Factor | Decision |
|---|---|
| **Choice** | Celery with Redis as broker and result backend |
| **Alternatives Considered** | Dramatiq, Huey, ARQ, asyncio background tasks |
| **Rationale** | Battle-tested for long-running tasks, native retry/backoff, rate limiting, priority queues, task chaining, monitoring (Flower) |
| **Development Mode** | Tasks can run synchronously in-process for development without spinning up workers |

---

## 5. Scheduler: APScheduler

| Factor | Decision |
|---|---|
| **Choice** | APScheduler integrated with Celery Beat |
| **Rationale** | Cron-like scheduling, interval scheduling, one-shot scheduling, persistent job store, timezone-aware |
| **Integration** | APScheduler triggers Celery tasks on schedule |

---

## 6. Scraping Gateway: Apify

| Factor | Decision |
|---|---|
| **Choice** | Apify API as the scraping infrastructure |
| **Rationale** | Managed scraping infrastructure, handles anti-bot measures, proxy rotation, browser rendering. Avoids legal/technical issues of direct scraping |
| **Abstraction** | Each job provider calls specific Apify actors. The provider interface ensures we can swap Apify for direct scraping or other services per-provider without changing business logic |

---

## 7. LLM Layer: Multi-Provider with Fallback

| Factor | Decision |
|---|---|
| **Primary** | OpenRouter (access to many models, including free tiers) |
| **Fallback 1** | OpenAI-compatible APIs |
| **Fallback 2** | Ollama (fully local, zero cost) |
| **Rationale** | No vendor lock-in. OpenRouter provides model diversity. Ollama enables offline/free usage. All providers implement the same interface |
| **Model Selection** | Configurable via `.env`. Default uses cost-effective models for routine tasks, stronger models for critical analysis |
| **Caching** | Aggressive LLM response caching keyed by (job_hash, task_type, resume_version) — never process the same job+task twice |

---

## 8. Embedding Strategy

| Factor | Decision |
|---|---|
| **Choice** | sentence-transformers (local) or API-based embeddings |
| **Model** | `all-MiniLM-L6-v2` (default, 384 dimensions, fast) |
| **Rationale** | Runs locally without API costs, small model size, good quality for semantic similarity |
| **Storage** | JSON array in database column. Sufficient for thousands of jobs. Can upgrade to pgvector for millions |
| **Similarity** | Cosine similarity computed in Python. For scale, can offload to database with pgvector |

---

## 9. Resume Parsing

| Factor | Decision |
|---|---|
| **Choice** | PyMuPDF (fitz) + pdfplumber |
| **Rationale** | PyMuPDF for fast text extraction, pdfplumber for table/layout parsing. Combined approach handles diverse resume formats |
| **Key Constraint** | Parse once, store structured JSON. All downstream consumers use the JSON, never re-parse the PDF |
| **Extraction** | Rule-based section detection with regex patterns. No LLM needed for parsing — keeps it fast and deterministic |

---

## 10. Reporting: Pandas + OpenPyXL

| Factor | Decision |
|---|---|
| **Choice** | Pandas for data manipulation, OpenPyXL for Excel generation |
| **Rationale** | Pandas provides powerful DataFrame operations for analytics. OpenPyXL gives full control over Excel formatting (conditional formatting, frozen panes, auto-sizing, hyperlinks) |
| **Output** | `.xlsx` files with multiple worksheets, each with distinct formatting and data filters |

---

## 11. Authentication: JWT

| Factor | Decision |
|---|---|
| **Choice** | JWT with bcrypt password hashing |
| **Library** | python-jose (JWT), passlib + bcrypt (hashing) |
| **Rationale** | Stateless authentication suitable for API-first architecture. No session storage needed |
| **Token Strategy** | Short-lived access tokens (30 min) + long-lived refresh tokens (7 days) |

---

## 12. Logging: structlog

| Factor | Decision |
|---|---|
| **Choice** | structlog with JSON output |
| **Rationale** | Structured logging enables machine-parseable logs for production monitoring. Context binding (request ID, user ID, provider name) automatically enriches every log entry |
| **Development** | Console renderer with colors for readability |
| **Production** | JSON renderer for log aggregation systems |

---

## 13. Dashboard: Jinja2 + HTMX

| Factor | Decision |
|---|---|
| **Choice** | Server-rendered HTML with HTMX for interactivity |
| **Alternatives Considered** | React SPA, Vue SPA, Svelte |
| **Rationale** | No separate frontend build process, no Node.js dependency, full-stack Python, HTMX provides SPA-like interactivity with zero JavaScript build tooling. Perfect for a single-user productivity tool |
| **Styling** | Vanilla CSS with a modern design system |

---

## 14. Testing Strategy

| Level | Tool | Coverage Target |
|---|---|---|
| **Unit Tests** | pytest + pytest-asyncio | Services, matching engine, providers |
| **Integration Tests** | pytest + httpx.AsyncClient | API endpoints, database operations |
| **Mocking** | pytest-mock, unittest.mock | External APIs (Apify, LLM providers) |
| **Fixtures** | conftest.py factories | Consistent test data generation |

---

## 15. Code Quality

| Tool | Purpose |
|---|---|
| **Black** | Code formatting (deterministic) |
| **Ruff** | Linting (replaces flake8 + isort + pylint) |
| **MyPy** | Static type checking |
| **Pre-commit** | Automated quality gates before every commit |

---

## 16. Containerization

| Component | Image |
|---|---|
| **App** | `python:3.12-slim` |
| **PostgreSQL** | `postgres:16-alpine` |
| **Redis** | `redis:7-alpine` |
| **Worker** | Same image as app, different entrypoint |

**Multi-stage builds** to minimize image size. Development and production compose configurations separated.

---

## 17. Key Architectural Patterns

| Pattern | Where Used | Why |
|---|---|---|
| **Repository Pattern** | Data access layer | Decouples business logic from ORM, enables testing with in-memory repos |
| **Service Layer** | Business logic | Single responsibility, dependency injection, testability |
| **Strategy Pattern** | Providers (job + LLM) | Pluggable implementations behind common interfaces |
| **Factory Pattern** | Provider registry | Dynamic provider instantiation based on configuration |
| **Observer Pattern** | Notifications | Decouple event generation from notification delivery |
| **Chain of Responsibility** | LLM fallback | Ordered provider chain with automatic failover |
| **Template Method** | Base provider classes | Common workflow with customizable steps |
| **Decorator Pattern** | Caching, retry, timing | Cross-cutting concerns without modifying business logic |

---

## 18. Non-Functional Requirements

| Requirement | Target | Implementation |
|---|---|---|
| **Startup Time** | < 5 seconds | Lazy loading of heavy modules (embeddings, LLM clients) |
| **API Response Time** | < 200ms (p95) | Database indexes, query optimization, Redis caching |
| **Job Processing** | 100+ jobs/minute | Concurrent provider searches, async I/O, batch database operations |
| **Memory Usage** | < 512MB (app) | Streaming processing, generator patterns, embedding model selection |
| **Disk Usage** | < 1GB (database) | Efficient storage, periodic cleanup of old data |
| **Availability** | Self-healing | Automatic retry, health checks, graceful degradation |
