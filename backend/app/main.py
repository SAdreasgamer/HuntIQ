"""
HuntIQ — Main FastAPI Application Entrypoint.

Initializes FastAPI app instance, CORS middleware, API routers, and lifecycle events.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config.settings import get_settings
from app.core.logging import get_logger
from app.database import init_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown lifecycle events."""
    logger.info("app_startup_begin")
    await init_db()
    logger.info("app_startup_complete")
    yield
    logger.info("app_shutdown_complete")


def create_application() -> FastAPI:
    """FastAPI application factory."""
    settings = get_settings()

    app = FastAPI(
        title="HuntIQ API",
        description="Autonomous AI-Powered Job Search Engine API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount v1 Router
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, Any]:
        """System health check status endpoint."""
        return {
            "status": "healthy",
            "app_name": "HuntIQ Engine",
            "version": "1.0.0",
            "environment": str(settings.app_env),
        }

    return app


app = create_application()
