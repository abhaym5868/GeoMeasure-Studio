"""
GeoMeasure Studio — FastAPI Application Entry Point

This module:
1. Creates the FastAPI app instance with metadata for OpenAPI docs.
2. Configures logging at startup (lifespan context manager).
3. Ensures runtime directories exist (uploads/, tmp/).
4. Registers exception handlers.
5. Configures CORS with an explicit origin whitelist.
6. Mounts all API routers.

Why a lifespan context manager instead of @app.on_event?
- on_event("startup"/"shutdown") is deprecated in FastAPI 0.95+.
- lifespan gives a clean async context where setup happens before
  yield and teardown happens after, matching Python's 'with' idiom.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health as health_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Code before 'yield' runs at startup.
    Code after 'yield' runs at shutdown.
    """
    settings = get_settings()

    # ── 1. Configure logging first — everything after this is logged ──
    configure_logging(
        log_level=settings.log_level,
        log_format=settings.log_format,
    )
    logger = get_logger(__name__)

    # ── 2. Ensure runtime directories exist ───────────────────────
    settings.ensure_directories()
    logger.info(
        "Application starting",
        version=settings.app_version,
        environment=settings.app_env,
        upload_dir=str(settings.upload_path),
        temp_dir=str(settings.temp_path),
    )

    yield  # ← Application is running

    # ── Shutdown ──────────────────────────────────────────────────
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    """
    Application factory — creates and configures the FastAPI instance.

    Using a factory function (rather than a module-level app = FastAPI())
    makes it trivial to create isolated app instances for testing.
    """
    settings = get_settings()

    app = FastAPI(
        title="GeoMeasure Studio",
        description=(
            "Geospatial File Measurement and Analysis Platform. "
            "Upload KML or Shapefile ZIP archives and receive accurate, "
            "CRS-aware measurements with interactive map visualization."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────
    # Allow only the configured frontend origins. In production, this
    # should be exactly the domain of the deployed frontend.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
        expose_headers=["Content-Disposition"],  # Required for file downloads
    )

    # ── Exception handlers ────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────
    # Health check is mounted at root (not under /api/) so load
    # balancers and container orchestrators can reach it easily.
    app.include_router(health_router.router)

    # Phase 3+ routers will be added here:
    # from app.api.routes import files, measurements, exports
    # app.include_router(files.router, prefix="/api")
    # app.include_router(measurements.router, prefix="/api")
    # app.include_router(exports.router, prefix="/api")

    return app


# ── Module-level app instance ─────────────────────────────────────
# Uvicorn imports this: `uvicorn app.main:app`
app = create_app()
