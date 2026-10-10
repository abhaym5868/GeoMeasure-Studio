"""
GeoMeasure Studio — Health Check Route

GET /health/

Returns:
- Overall application status ('ok' or 'degraded')
- Database connectivity status (tested with a real query)
- Application version and environment

Design notes:
- Database check issues a lightweight 'SELECT 1' query.
- If DB is unreachable, the endpoint still returns 200 with
  status='degraded' and db='error' — it does NOT return 500.
  This makes health checks more useful for load balancers and
  monitoring tools that expect 200 from a reporting endpoint.
- Never expose connection strings, passwords, or internal paths
  in the response.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.common import HealthStatus

router = APIRouter(tags=["Health"])
logger = get_logger(__name__)
settings = get_settings()


@router.get(
    "/health/",
    response_model=HealthStatus,
    summary="Application health check",
    description=(
        "Returns the operational status of the application and its database connection. "
        "Always returns HTTP 200. Check the 'status' field for 'ok' or 'degraded'."
    ),
)
async def health_check(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HealthStatus:
    """
    Perform a lightweight health check.

    The database check executes 'SELECT 1' to confirm the connection
    pool can reach PostgreSQL. All other failures are caught and
    reported safely without exposing internal details.
    """
    db_status = "ok"
    db_error: str | None = None
    overall = "ok"

    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        logger.debug("Health check: database is reachable")
    except Exception as exc:
        db_status = "error"
        overall = "degraded"
        # Safe error: report the type of failure, not credentials or paths
        db_error = f"Database connectivity check failed: {type(exc).__name__}"
        logger.warning(
            "Health check: database unreachable",
            error_type=type(exc).__name__,
            exc_info=True,
        )

    return HealthStatus(
        status=overall,
        version=settings.app_version,
        db=db_status,
        db_error=db_error,
        environment=settings.app_env,
    )
