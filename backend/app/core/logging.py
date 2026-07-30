"""
HuntIQ — Structured Logging Configuration.

Sets up structlog with appropriate renderers for development
(colored console) and production (JSON) environments.

Usage:
    from app.core.logging import get_logger

    logger = get_logger(__name__)
    logger.info("job_found", company="Google", role="Backend Engineer")
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from app.config.settings import Settings


def setup_logging(settings: Settings) -> None:
    """
    Configure structured logging for the application.

    Args:
        settings: Application settings for log level and environment.
    """
    log_level = settings.log_level.value
    is_dev = settings.is_development

    # Shared processors for all environments
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if is_dev:
        # Development: colored console output
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer(
            colors=True,
            pad_event=40,
        )
    else:
        # Production: JSON output for log aggregation
        shared_processors.append(structlog.processors.format_exc_info)
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure the standard library root logger
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Silence noisy third-party loggers
    for noisy_logger in ("uvicorn.access", "httpx", "httpcore", "aiosqlite"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger bound with the given name.

    Args:
        name: Logger name (typically __name__).

    Returns:
        A bound structlog logger instance.
    """
    return structlog.get_logger(name)
