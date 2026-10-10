"""
GeoMeasure Studio — Structured Logging

Uses structlog to produce consistent, machine-readable JSON logs in
production and developer-friendly colored console output in development.

Why structlog?
- Every log event is a dict — easy to search in Loki, CloudWatch, etc.
- Processors can be swapped without changing callsites.
- Context variables (request_id, file_id) can be bound to the local
  context and will appear on every log line within that scope.

Usage:
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("File uploaded", file_id=str(file_id), size_bytes=1234)
"""
from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    pass


def configure_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """
    Configure structlog and the standard library logging bridge.

    Call this ONCE at application startup (in main.py lifespan).

    Args:
        log_level: One of DEBUG, INFO, WARNING, ERROR, CRITICAL.
        log_format: 'json' for structured output, 'console' for dev.
    """
    # ── Standard library logging → structlog bridge ───────────────
    # Third-party libraries (uvicorn, sqlalchemy, etc.) use stdlib
    # logging. This handler ensures their output also flows through
    # our structlog processors for consistent formatting.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    # Silence noisy loggers that we don't need in most environments
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # ── Shared pre-chain processors ───────────────────────────────
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,  # Merge bound context vars
        structlog.stdlib.add_logger_name,         # Add 'logger' field
        structlog.stdlib.add_log_level,           # Add 'level' field
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),  # ISO 8601 timestamp
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "json":
        # ── Production: JSON lines ─────────────────────────────────
        # Each log event is a single JSON object on one line.
        # Tools like Loki, CloudWatch, and Datadog parse these natively.
        renderer = structlog.processors.JSONRenderer()
    else:
        # ── Development: colored console output ───────────────────
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors
        + [
            # Format exceptions as a string field in the JSON object
            structlog.processors.ExceptionRenderer(),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Return a structlog BoundLogger.

    The name is typically __name__ from the calling module, which gives
    each logger a qualified name like 'app.services.analysis_service'.
    """
    return structlog.get_logger(name)
