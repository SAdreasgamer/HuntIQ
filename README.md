# HuntIQ

> AI-Powered Recruitment Intelligence Platform

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

HuntIQ is a fully automated, AI-powered job search and recruitment intelligence platform. It continuously searches job boards, intelligently matches opportunities against your resume using a hybrid scoring engine, tracks applications, generates reports, and delivers notifications — all with minimal manual intervention.

## Key Features

- **Multi-Source Job Search** — LinkedIn, Indeed, Greenhouse, Lever, Ashby, Wellfound, Naukri, Company Career Pages (via Apify)
- **Hybrid Matching Engine** — Rule-based scoring + embedding similarity + LLM analysis
- **Resume Intelligence** — Parse once, match everywhere. Support multiple resume versions
- **Application Tracker** — Full lifecycle tracking from discovery to offer/rejection
- **AI-Powered Insights** — Match explanations, skill gap analysis, cover letters, interview prep
- **Automated Reports** — Beautiful Excel reports with conditional formatting
- **Smart Notifications** — Email, desktop, webhook — only for high-value matches
- **Company Intelligence** — Track hiring patterns, tech stacks, salary ranges
- **Analytics Dashboard** — Trends, conversion rates, skill demand analysis

## Architecture

- **Plugin Architecture** — Add job providers and LLM providers without modifying existing code
- **Pipeline Architecture** — Composable, decoupled processing pipelines
- **Repository Pattern** — Clean separation of data access from business logic
- **Event-Driven** — Background workers for long-running tasks (Celery + Redis)
- **Configuration-Driven** — Everything configurable via `.env`

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic v2 |
| Database | PostgreSQL (prod), SQLite (dev) |
| ORM | SQLAlchemy 2.0, Alembic |
| Cache/Broker | Redis |
| Task Queue | Celery |
| Scheduler | APScheduler |
| Scraping | Apify API |
| LLM | OpenRouter, OpenAI-compatible, Ollama |
| Reports | Pandas, OpenPyXL |
| Dashboard | Jinja2, HTMX |
| Containerization | Docker, Docker Compose |

## Documentation

- [System Architecture](docs/architecture/ARCHITECTURE.md)
- [Data Flow Specification](docs/architecture/DATA_FLOW.md)
- [Technology Decisions](docs/architecture/TECH_DECISIONS.md)

## License

MIT
