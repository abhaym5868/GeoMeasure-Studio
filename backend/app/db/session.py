"""
GeoMeasure Studio — SQLAlchemy Async Session Factory

This module creates and manages the async database engine and session factory.
It does NOT import any ORM models directly — that happens in db/base.py so
Alembic can discover all models through a single import.

Key design decisions:
- We use asyncpg as the async driver (fast C extension, no GIL for I/O).
- pool_pre_ping=True ensures stale connections are detected and replaced
  automatically, preventing 'connection closed' errors after PostgreSQL
  restarts or idle timeouts.
- Sessions are scoped per HTTP request via FastAPI dependency injection
  (get_db dependency below). No global mutable session state.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

# ── Engine ────────────────────────────────────────────────────────
# Created once at import time. The connection pool is managed by
# asyncpg and SQLAlchemy's async pool machinery.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,          # Log SQL statements only in debug mode
    pool_pre_ping=True,           # Detect and replace stale connections
    pool_size=10,                 # Default pool size
    max_overflow=20,              # Extra connections under load
    pool_timeout=30,              # Seconds to wait for a connection
    pool_recycle=1800,            # Recycle connections every 30 minutes
)

# ── Session factory ───────────────────────────────────────────────
# expire_on_commit=False: keep ORM objects usable after a commit
# without issuing new SELECT queries. Important in async contexts
# where lazy loading is not supported.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ── FastAPI dependency ────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session per request.

    Usage in a route:
        @router.get("/something")
        async def my_handler(db: AsyncSession = Depends(get_db)):
            ...

    The session is automatically committed on success and rolled back
    on exception, then closed in the finally block.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
