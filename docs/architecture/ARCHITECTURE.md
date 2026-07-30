# HuntIQ — System Architecture

> AI-Powered Recruitment Intelligence Platform

---

## 1. System Overview

HuntIQ is a fully automated, AI-powered job search and recruitment intelligence platform. It continuously scrapes job boards, matches opportunities against parsed resumes using a hybrid scoring engine (rule-based + embedding similarity + LLM analysis), tracks applications, generates reports, and delivers intelligent notifications — all with minimal manual intervention.

### Core Design Principles

| Principle | Application |
|---|---|
| **Plugin Architecture** | Every job provider, LLM provider, and notification channel is a pluggable module implementing a common interface |
| **Pipeline Architecture** | Resume parsing, job normalization, matching, and scoring flow through composable, decoupled pipelines |
| **Repository Pattern** | All database access is abstracted behind repository interfaces, enabling testability and swappable backends |
| **Service Layer** | Business logic lives in services, never in API routes or repositories |
| **Event-Driven** | Background workers process jobs asynchronously via Celery + Redis |
| **Configuration-Driven** | All behavior is configurable via `.env` without code changes |
| **Cache-First** | LLM outputs, embeddings, and provider health states are cached aggressively |
| **Fail-Safe** | Every external call implements retries, exponential backoff, circuit breakers, and fallback chains |

---

## 2. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HuntIQ Platform                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │  FastAPI App  │    │  Dashboard   │    │  OpenAPI / Swagger   │  │
│  │  (REST API)   │◄──►│  (Jinja2 +   │    │  Documentation       │  │
│  │              │    │   HTMX)      │    │                      │  │
│  └──────┬───────┘    └──────────────┘    └──────────────────────┘  │
│         │                                                           │
│  ┌──────▼───────────────────────────────────────────────────────┐  │
│  │                      Service Layer                            │  │
│  │                                                               │  │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐   │  │
│  │  │ Search  │ │ Matching │ │ Resume   │ │ Application    │   │  │
│  │  │ Service │ │ Engine   │ │ Service  │ │ Tracker        │   │  │
│  │  └────┬────┘ └─────┬────┘ └─────┬────┘ └───────┬────────┘   │  │
│  │       │            │            │               │             │  │
│  │  ┌────▼────┐ ┌─────▼────┐ ┌────▼─────┐ ┌──────▼─────────┐  │  │
│  │  │Analytics│ │ LLM      │ │ Report   │ │ Notification   │  │  │
│  │  │ Engine  │ │ Service  │ │ Generator│ │ Service        │  │  │
│  │  └─────────┘ └──────────┘ └──────────┘ └────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Repository Layer                            │  │
│  │                                                               │  │
│  │  JobRepo │ CompanyRepo │ ApplicationRepo │ ResumeRepo │ ...  │  │
│  └──────────────────────────┬────────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────▼───────────────────────────────────┐  │
│  │                     Database Layer                             │  │
│  │           PostgreSQL (prod) │ SQLite (dev)                    │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                  Background Workers                           │  │
│  │                                                               │  │
│  │  ┌───────────┐  ┌────────────┐  ┌──────────────────────┐    │  │
│  │  │  Celery   │  │ APScheduler│  │  Redis (Broker +     │    │  │
│  │  │  Workers  │  │            │  │  Cache + Rate Limit) │    │  │
│  │  └───────────┘  └────────────┘  └──────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                  Provider Layer (Plugins)                     │  │
│  │                                                               │  │
│  │  ┌──────────┐ ┌───────────┐ ┌───────┐ ┌───────┐ ┌────────┐ │  │
│  │  │ LinkedIn │ │Greenhouse │ │ Lever │ │ Ashby │ │ Indeed │ │  │
│  │  └──────────┘ └───────────┘ └───────┘ └───────┘ └────────┘ │  │
│  │  ┌──────────┐ ┌───────────┐ ┌──────────────────────────┐   │  │
│  │  │Wellfound │ │  Naukri   │ │  Company Career Pages    │   │  │
│  │  └──────────┘ └───────────┘ └──────────────────────────┘   │  │
│  │                       │                                     │  │
│  │              ┌────────▼─────────┐                           │  │
│  │              │   Apify Client   │                           │  │
│  │              │  (HTTP Gateway)  │                           │  │
│  │              └──────────────────┘                           │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    LLM Layer (Plugins)                        │  │
│  │                                                               │  │
│  │  ┌────────────┐  ┌────────────────┐  ┌──────────────────┐   │  │
│  │  │ OpenRouter │  │ OpenAI-compat  │  │     Ollama       │   │  │
│  │  │ (Primary)  │  │                │  │  (Local Models)  │   │  │
│  │  └────────────┘  └────────────────┘  └──────────────────┘   │  │
│  │                       │                                     │  │
│  │              ┌────────▼─────────┐                           │  │
│  │              │  LLM Response    │                           │  │
│  │              │     Cache        │                           │  │
│  │              └──────────────────┘                           │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Architecture

### 3.1 API Layer

| Component | Technology | Responsibility |
|---|---|---|
| REST API | FastAPI | All CRUD operations, search, filtering, pagination |
| Dashboard | Jinja2 + HTMX | Server-rendered interactive dashboard |
| Authentication | JWT (python-jose) | Token-based auth with bcrypt password hashing |
| Validation | Pydantic v2 | Request/response validation and serialization |
| Documentation | OpenAPI 3.1 | Auto-generated Swagger/ReDoc |

### 3.2 Service Layer

Services encapsulate all business logic. They are injected into API routes via FastAPI's dependency injection.

| Service | Responsibility |
|---|---|
| `SearchService` | Orchestrates concurrent job searches across providers |
| `MatchingService` | Runs the hybrid matching pipeline (rules → embeddings → LLM) |
| `ResumeService` | Parses, stores, and manages resume versions and embeddings |
| `JobService` | Normalizes, deduplicates, and manages job lifecycle |
| `ApplicationService` | Tracks application stages and history |
| `BookmarkService` | Manages bookmarks, tags, priorities, reminders |
| `CompanyService` | Maintains company intelligence and hiring patterns |
| `AnalyticsService` | Generates statistics, trends, and insights |
| `ReportService` | Generates Excel reports with formatted worksheets |
| `NotificationService` | Routes notifications through configured channels |
| `LLMService` | Orchestrates LLM tasks with caching and fallback |
| `PreferenceService` | Manages user configuration and search parameters |

### 3.3 Provider Layer (Plugin Architecture)

Every external integration implements a common abstract interface.

```
                    ┌──────────────────────┐
                    │  JobProvider (ABC)   │
                    │                      │
                    │  + search_jobs()     │
                    │  + normalize_job()   │
                    │  + validate()        │
                    │  + health_check()    │
                    └──────────┬───────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
    ┌───────▼───────┐ ┌───────▼───────┐ ┌────────▼──────┐
    │ LinkedInProv  │ │ GreenhouseProv│ │  LeverProv    │
    └───────────────┘ └───────────────┘ └───────────────┘
            ... (8 providers total)
```

**Adding a new provider** requires:
1. Create `app/scrapers/providers/new_provider.py`
2. Implement `JobProvider` interface
3. Register in provider registry via decorator or config

No modification to existing code required (Open-Closed Principle).

### 3.4 LLM Layer (Plugin Architecture)

```
                    ┌──────────────────────┐
                    │  LLMProvider (ABC)   │
                    │                      │
                    │  + explain_match()   │
                    │  + summarize_job()   │
                    │  + missing_skills()  │
                    │  + cover_letter()    │
                    │  + interview_prep()  │
                    │  + ...               │
                    └──────────┬───────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
    ┌───────▼───────┐ ┌───────▼───────┐ ┌────────▼──────┐
    │  OpenRouter   │ │ OpenAI-compat │ │    Ollama     │
    │  (Primary)    │ │               │ │  (Local)      │
    └───────────────┘ └───────────────┘ └───────────────┘
```

**Fallback Chain:** OpenRouter → OpenAI-Compatible → Ollama

### 3.5 Matching Engine

The matching engine uses a three-stage pipeline:

```
┌─────────────────────────────────────────────────────────┐
│                   Matching Pipeline                      │
│                                                         │
│  Stage 1: Rule-Based Scoring                            │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Skills Match    (weighted)                        │  │
│  │ Role Match      (weighted)                        │  │
│  │ Experience      (weighted)                        │  │
│  │ Location        (weighted)                        │  │
│  │ Tech Stack      (weighted)                        │  │
│  │ Keywords        (weighted)                        │  │
│  │ Company Pref    (weighted)                        │  │
│  │ Blacklist Check (disqualifier)                    │  │
│  │                                                   │  │
│  │ Output: Score 0–100                               │  │
│  └───────────────────────┬───────────────────────────┘  │
│                          │                               │
│                          ▼                               │
│  Stage 2: Embedding Similarity                           │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Resume Embedding  ←→  Job Embedding               │  │
│  │ Cosine Similarity                                 │  │
│  │                                                   │  │
│  │ Output: Similarity 0.0–1.0                        │  │
│  └───────────────────────┬───────────────────────────┘  │
│                          │                               │
│                    (threshold gate)                       │
│                          │                               │
│                          ▼                               │
│  Stage 3: LLM Analysis (conditional)                     │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Input: Structured Resume JSON + Job JSON          │  │
│  │ (NEVER raw PDF)                                   │  │
│  │                                                   │  │
│  │ Output:                                           │  │
│  │   - Match explanation                             │  │
│  │   - Missing skills                                │  │
│  │   - Shortlist probability                         │  │
│  │   - Apply recommendation                          │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  Final Score = w1*RuleScore + w2*EmbeddingSim + w3*LLM  │
└─────────────────────────────────────────────────────────┘
```

### 3.6 Resume Pipeline

```
Resume PDF  →  Parser (PyMuPDF + pdfplumber)
                    │
                    ▼
            Structured Resume JSON
            {
              skills, projects, experience,
              education, certifications,
              technologies, achievements, keywords
            }
                    │
                    ▼
            Embedding Generator
            (sentence-transformers / API)
                    │
                    ▼
            Database Storage
            (resume_versions, resume_skills,
             resume_embeddings)
```

**Key constraint:** The PDF is parsed **exactly once**. All downstream consumers (matching, LLM, reports) use the stored structured JSON.

### 3.7 Job Pipeline

```
Apify API Response  →  Provider.normalize_job()
                              │
                              ▼
                    Structured Job JSON
                    {
                      company, role, skills,
                      responsibilities, location,
                      salary, experience, tech_stack,
                      description, requirements
                    }
                              │
                              ▼
                    Deduplication Engine
                    (company + role + URL + desc similarity)
                              │
                              ▼
                    Embedding Generator
                              │
                              ▼
                    Database Storage
                    (jobs, job_skills, job_embeddings)
```

### 3.8 Background Processing

```
┌─────────────────────────────────────────────────┐
│              APScheduler                         │
│                                                 │
│  ┌──────────────────────────────────────────┐   │
│  │ Cron: Search Jobs         (configurable) │   │
│  │ Cron: Refresh Closed Jobs (daily)        │   │
│  │ Cron: Generate Reports    (daily)        │   │
│  │ Cron: Analytics Snapshot  (daily)        │   │
│  │ Cron: Send Notifications  (on event)     │   │
│  │ Cron: Health Checks       (hourly)       │   │
│  └────────────────────┬─────────────────────┘   │
│                       │                         │
│              Enqueues tasks to                   │
│                       │                         │
│              ┌────────▼─────────┐               │
│              │   Redis Queue    │               │
│              └────────┬─────────┘               │
│                       │                         │
│              ┌────────▼─────────┐               │
│              │  Celery Workers  │               │
│              │                  │               │
│              │  - search_task   │               │
│              │  - match_task    │               │
│              │  - llm_task      │               │
│              │  - report_task   │               │
│              │  - notify_task   │               │
│              └──────────────────┘               │
└─────────────────────────────────────────────────┘
```

---

## 4. Database Architecture

### 4.1 Entity Relationship Overview

```
┌──────────┐     ┌──────────┐     ┌─────────────┐
│  Users   │────►│Preferences│    │Resume       │
└──────────┘     └──────────┘     │Versions     │
     │                             └──────┬──────┘
     │                                    │
     │           ┌────────────────────────┤
     │           │                        │
     ▼           ▼                        ▼
┌──────────┐  ┌──────────┐     ┌─────────────┐
│Companies │  │  Jobs    │◄───►│Resume Skills │
└────┬─────┘  └────┬─────┘     └─────────────┘
     │              │
     │         ┌────┴─────────────┐
     │         │                  │
     ▼         ▼                  ▼
┌──────────┐ ┌──────────────┐ ┌──────────┐
│Recruiters│ │Applications  │ │Bookmarks │
└──────────┘ └──────────────┘ └──────────┘
                                   │
                              ┌────┴────┐
                              ▼         ▼
                        ┌────────┐ ┌────────┐
                        │ Tags   │ │Notes   │
                        └────────┘ └────────┘
```

### 4.2 Core Tables

| Table | Purpose |
|---|---|
| `users` | Authentication and user identity |
| `user_preferences` | Search config, thresholds, blacklists |
| `companies` | Company intelligence and metadata |
| `jobs` | Normalized job listings |
| `job_skills` | Skills extracted from job descriptions |
| `job_sources` | Tracks which provider found each job |
| `job_embeddings` | Vector embeddings for semantic matching |
| `resume_versions` | Multiple resume variants per user |
| `resume_skills` | Skills extracted from each resume version |
| `resume_embeddings` | Vector embeddings for each resume version |
| `applications` | Application tracking with stage history |
| `application_stages` | Stage transition log |
| `bookmarks` | Saved jobs with priority and reminders |
| `bookmark_tags` | Tag associations for bookmarks |
| `recruiters` | Recruiter contacts linked to companies |
| `notifications` | Notification history and delivery status |
| `reports` | Generated report metadata and file paths |
| `analytics_snapshots` | Daily/weekly/monthly aggregated metrics |
| `llm_cache` | Cached LLM responses keyed by hash |
| `search_checkpoints` | Resume interrupted searches |

---

## 5. Security Architecture

```
┌─────────────────────────────────────────────────┐
│                Security Layers                   │
│                                                 │
│  Layer 1: Authentication                        │
│  ├── JWT access tokens (short-lived)            │
│  ├── JWT refresh tokens (long-lived)            │
│  └── bcrypt password hashing                    │
│                                                 │
│  Layer 2: Authorization                         │
│  └── User-scoped data isolation                 │
│                                                 │
│  Layer 3: Input Validation                      │
│  ├── Pydantic v2 models on all endpoints        │
│  └── Parameterized queries (SQLAlchemy ORM)     │
│                                                 │
│  Layer 4: Transport                             │
│  ├── CORS whitelist                             │
│  └── Rate limiting (Redis-backed)               │
│                                                 │
│  Layer 5: Secrets                               │
│  ├── .env file (never committed)                │
│  ├── Docker secrets                             │
│  └── No secrets in code or logs                 │
└─────────────────────────────────────────────────┘
```

---

## 6. Observability Architecture

| Concern | Implementation |
|---|---|
| **Structured Logging** | `structlog` with JSON output, correlation IDs |
| **Request Tracing** | Middleware injects `X-Request-ID` into every request |
| **Health Checks** | `/health` endpoint checks DB, Redis, Celery, providers |
| **Metrics** | Execution timing decorators, provider success/failure rates |
| **Error Tracking** | Structured error payloads with context |

---

## 7. Deployment Architecture

```
┌──────────────────────────────────────────────────┐
│              Docker Compose Stack                 │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ FastAPI  │  │  Celery  │  │ Celery Beat   │  │
│  │   App    │  │  Worker  │  │ (Scheduler)   │  │
│  │ :8000    │  │          │  │               │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
│                                                  │
│  ┌──────────┐  ┌──────────┐                      │
│  │PostgreSQL│  │  Redis   │                      │
│  │  :5432   │  │  :6379   │                      │
│  └──────────┘  └──────────┘                      │
└──────────────────────────────────────────────────┘
```

### Development Mode

- **Database:** SQLite (zero configuration)
- **Cache:** Redis (or in-memory fallback)
- **Workers:** In-process (no separate Celery process required)
- **Hot Reload:** FastAPI with `--reload`

### Production Mode

- **Database:** PostgreSQL
- **Cache:** Redis
- **Workers:** Celery with Redis broker
- **Scheduler:** Celery Beat with APScheduler
- **Reverse Proxy:** Configurable (Nginx/Caddy)

---

## 8. Configuration Architecture

All configuration flows through a single, validated Pydantic `Settings` class:

```
.env file
    │
    ▼
Pydantic Settings
    │
    ├── DatabaseSettings
    │     ├── DB_TYPE (sqlite / postgresql)
    │     ├── DB_HOST, DB_PORT, DB_NAME
    │     ├── DB_USER, DB_PASSWORD
    │     └── DB_ECHO (SQL logging)
    │
    ├── RedisSettings
    │     ├── REDIS_URL
    │     └── REDIS_TTL
    │
    ├── ApifySettings
    │     └── APIFY_TOKEN
    │
    ├── LLMSettings
    │     ├── LLM_PROVIDER (openrouter / openai / ollama)
    │     ├── LLM_MODEL
    │     ├── LLM_API_KEY
    │     ├── LLM_BASE_URL
    │     ├── LLM_FALLBACK_PROVIDER
    │     ├── LLM_FALLBACK_MODEL
    │     └── LLM_CACHE_TTL
    │
    ├── SearchSettings
    │     ├── SEARCH_KEYWORDS (list)
    │     ├── SEARCH_LOCATIONS (list)
    │     ├── SEARCH_FREQUENCY_HOURS
    │     └── MATCH_THRESHOLD
    │
    ├── NotificationSettings
    │     ├── NOTIFY_EMAIL
    │     ├── NOTIFY_WEBHOOK_URL
    │     └── NOTIFY_THRESHOLD
    │
    ├── SecuritySettings
    │     ├── SECRET_KEY
    │     ├── ACCESS_TOKEN_EXPIRE_MINUTES
    │     ├── REFRESH_TOKEN_EXPIRE_DAYS
    │     └── CORS_ORIGINS
    │
    └── AppSettings
          ├── APP_NAME
          ├── APP_ENV (dev / staging / prod)
          ├── DEBUG
          └── LOG_LEVEL
```

---

## 9. Error Handling Strategy

| Layer | Strategy |
|---|---|
| **API Routes** | FastAPI exception handlers → structured JSON error responses |
| **Services** | Custom exception hierarchy (`HuntIQError` → `ProviderError`, `MatchingError`, etc.) |
| **Providers** | Per-provider error handling with retry + fallback |
| **Background Tasks** | Celery retry policies with exponential backoff, dead-letter logging |
| **External APIs** | HTTPX with configurable timeouts, retry counts, backoff multipliers |

### Exception Hierarchy

```
HuntIQError (base)
├── ConfigurationError
├── DatabaseError
├── ProviderError
│   ├── ProviderTimeoutError
│   ├── ProviderRateLimitError
│   └── ProviderUnavailableError
├── MatchingError
├── ResumeParsingError
├── LLMError
│   ├── LLMTimeoutError
│   ├── LLMRateLimitError
│   └── LLMUnavailableError
├── NotificationError
├── AuthenticationError
└── AuthorizationError
```

---

## 10. Rate Limiting Strategy

| Resource | Strategy |
|---|---|
| **Apify API** | Token bucket per provider, configurable RPM |
| **LLM APIs** | Sliding window rate limiter, provider-specific limits |
| **API Endpoints** | Redis-backed rate limiter middleware |
| **Background Tasks** | Celery rate limiting per queue |

---

## 11. Data Flow Summary

### Job Discovery Flow
```
Scheduler triggers → Search Service → Provider Registry
→ Concurrent provider searches → Normalize → Deduplicate
→ Store → Embed → Match → Score → Notify (if threshold met)
```

### Resume Upload Flow
```
Upload PDF → Parse (once) → Extract structured JSON
→ Store JSON + metadata → Generate embeddings
→ Store embeddings → Re-score existing jobs (optional)
```

### Application Tracking Flow
```
User applies → Create application record → Track stage changes
→ Log stage transitions → Update analytics → Generate reports
```

### Report Generation Flow
```
Scheduler triggers → Query analytics data → Build dataframes
→ Generate Excel with formatting → Store report → Notify user
```
