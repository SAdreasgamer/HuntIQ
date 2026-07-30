.PHONY: help install install-dev install-prod lint format typecheck test test-unit test-integration clean run worker beat migrate revision

# ============================================================
# HuntIQ — Development Commands
# ============================================================

PYTHON := python3.12
VENV := .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
BLACK := $(VENV)/bin/black
RUFF := $(VENV)/bin/ruff
MYPY := $(VENV)/bin/mypy
UVICORN := $(VENV)/bin/uvicorn
CELERY := $(VENV)/bin/celery
ALEMBIC := $(VENV)/bin/alembic
PRECOMMIT := $(VENV)/bin/pre-commit

help: ## Show this help message
	@echo "HuntIQ — Development Commands"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================
# Environment Setup
# ============================================================

venv: ## Create virtual environment
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel

install: venv ## Install base dependencies
	$(PIP) install -r requirements/base.txt
	$(PIP) install -e .

install-dev: venv ## Install development dependencies
	$(PIP) install -r requirements/dev.txt
	$(PIP) install -e ".[dev]"
	$(PRECOMMIT) install

install-prod: venv ## Install production dependencies
	$(PIP) install -r requirements/prod.txt
	$(PIP) install -e ".[prod]"

# ============================================================
# Code Quality
# ============================================================

lint: ## Run ruff linter
	$(RUFF) check backend/

format: ## Format code with black and ruff
	$(BLACK) backend/
	$(RUFF) check --fix backend/

typecheck: ## Run mypy type checker
	$(MYPY) backend/app/

quality: format lint typecheck ## Run all code quality checks

# ============================================================
# Testing
# ============================================================

test: ## Run all tests
	$(PYTEST) backend/tests/

test-unit: ## Run unit tests only
	$(PYTEST) backend/tests/unit/ -m unit

test-integration: ## Run integration tests only
	$(PYTEST) backend/tests/integration/ -m integration

test-cov: ## Run tests with coverage report
	$(PYTEST) backend/tests/ --cov=app --cov-report=html --cov-report=term-missing

# ============================================================
# Application
# ============================================================

run: ## Start FastAPI development server
	cd backend && $(UVICORN) app.core.application:create_app --factory --reload --host 0.0.0.0 --port 8000

worker: ## Start Celery worker
	cd backend && $(CELERY) -A app.workers.celery_app worker --loglevel=info

beat: ## Start Celery beat scheduler
	cd backend && $(CELERY) -A app.workers.celery_app beat --loglevel=info

# ============================================================
# Database
# ============================================================

migrate: ## Run database migrations
	cd backend && $(ALEMBIC) upgrade head

revision: ## Create a new migration revision
	cd backend && $(ALEMBIC) revision --autogenerate -m "$(msg)"

downgrade: ## Downgrade database by one revision
	cd backend && $(ALEMBIC) downgrade -1

db-reset: ## Reset database (drop all, recreate)
	cd backend && $(ALEMBIC) downgrade base
	cd backend && $(ALEMBIC) upgrade head

# ============================================================
# Docker
# ============================================================

docker-build: ## Build Docker images
	docker compose build

docker-up: ## Start all services
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

docker-logs: ## Tail service logs
	docker compose logs -f

# ============================================================
# Cleanup
# ============================================================

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name .coverage -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/
