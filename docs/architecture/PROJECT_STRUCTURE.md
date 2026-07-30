# HuntIQ — Project Structure

```
huntiq/
│
├── README.md                              # Project overview and documentation
│
├── backend/                               # Backend application root
│   │
│   ├── alembic/                           # Database migration scripts (Alembic)
│   │   └── versions/                      # Generated migration files
│   │
│   ├── app/                               # Main application package
│   │   ├── __init__.py                    # App version and metadata
│   │   │
│   │   ├── api/                           # API layer (FastAPI routes)
│   │   │   ├── __init__.py
│   │   │   ├── dependencies/              # Dependency injection providers
│   │   │   │   └── __init__.py
│   │   │   ├── middleware/                # Request middleware
│   │   │   │   └── __init__.py
│   │   │   └── routes/                    # Route handlers by domain
│   │   │       └── __init__.py
│   │   │
│   │   ├── config/                        # Configuration management
│   │   │   └── __init__.py
│   │   │
│   │   ├── core/                          # Core application components
│   │   │   └── __init__.py                # App factory, exceptions, events
│   │   │
│   │   ├── database/                      # Database layer
│   │   │   └── __init__.py                # Engine, sessions, base model
│   │   │
│   │   ├── models/                        # SQLAlchemy ORM models
│   │   │   └── __init__.py
│   │   │
│   │   ├── schemas/                       # Pydantic v2 schemas
│   │   │   └── __init__.py
│   │   │
│   │   ├── repositories/                  # Repository layer (data access)
│   │   │   └── __init__.py
│   │   │
│   │   ├── services/                      # Service layer (business logic)
│   │   │   └── __init__.py
│   │   │
│   │   ├── scrapers/                      # Job scraper layer
│   │   │   ├── __init__.py                # Provider interface, registry
│   │   │   └── providers/                 # Individual provider implementations
│   │   │       └── __init__.py
│   │   │
│   │   ├── matcher/                       # Hybrid matching engine
│   │   │   └── __init__.py
│   │   │
│   │   ├── resume/                        # Resume processing pipeline
│   │   │   └── __init__.py
│   │   │
│   │   ├── llm/                           # LLM integration layer
│   │   │   ├── __init__.py
│   │   │   ├── prompts/                   # Prompt templates
│   │   │   └── providers/                 # LLM provider implementations
│   │   │       └── __init__.py
│   │   │
│   │   ├── analytics/                     # Analytics engine
│   │   │   └── __init__.py
│   │   │
│   │   ├── reports/                       # Excel report generator
│   │   │   └── __init__.py
│   │   │
│   │   ├── notifications/                 # Notification service
│   │   │   ├── __init__.py
│   │   │   └── channels/                  # Channel implementations
│   │   │       └── __init__.py
│   │   │
│   │   ├── scheduler/                     # APScheduler configuration
│   │   │   └── __init__.py
│   │   │
│   │   ├── workers/                       # Celery task definitions
│   │   │   └── __init__.py
│   │   │
│   │   ├── utils/                         # Shared utilities
│   │   │   └── __init__.py
│   │   │
│   │   ├── templates/                     # Jinja2 dashboard templates
│   │   │
│   │   └── static/                        # Static assets (CSS, JS, images)
│   │
│   └── tests/                             # Test suite
│       ├── __init__.py
│       ├── unit/                           # Unit tests
│       │   └── __init__.py
│       └── integration/                   # Integration tests
│           └── __init__.py
│
├── docs/                                  # Documentation
│   └── architecture/                      # Architecture decision records
│       ├── ARCHITECTURE.md
│       ├── DATA_FLOW.md
│       └── TECH_DECISIONS.md
│
├── docker/                                # Docker configuration
│
└── scripts/                               # Operational scripts
```

## Package Dependency Graph

```
api/
 └── depends on → services/
                    └── depends on → repositories/
                                      └── depends on → models/ + database/

scrapers/
 └── depends on → config/ (Apify settings)

matcher/
 └── depends on → services/ (resume, job)
                  llm/ (for Stage 3)

llm/
 └── depends on → config/ (LLM settings)

workers/
 └── depends on → services/ (all)

scheduler/
 └── depends on → workers/ (task dispatch)

reports/
 └── depends on → repositories/ (data queries)

notifications/
 └── depends on → config/ (notification settings)

analytics/
 └── depends on → repositories/ (data queries)
```

## Key Conventions

1. **Every directory under `app/` is a Python package** with an `__init__.py`
2. **No circular imports** — dependency flows top-down as shown above
3. **Config is centralized** — only `config/` reads environment variables
4. **Models are passive** — no business logic in ORM models
5. **Repositories are thin** — CRUD + custom queries, no business logic
6. **Services are fat** — all business logic lives here
7. **Routes are thin** — validation, dependency injection, delegation to services
