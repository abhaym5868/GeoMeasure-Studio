"""
Phase 2 Tests — conftest.py

Shared fixtures for all tests. Creates an isolated FastAPI test client
and a separate test database connection. Tests must not touch the
development database.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app


@pytest.fixture(scope="session")
def settings():
    """Return application settings (cached singleton)."""
    return get_settings()


@pytest.fixture(scope="session")
def app(settings):
    """Create a fresh FastAPI app instance for the test session."""
    test_app = create_app()

    # Use NullPool for tests so asyncpg connections aren't bound to a stale event loop
    test_engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
    )
    test_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    test_app.dependency_overrides[get_db] = _override_get_db
    return test_app


@pytest_asyncio.fixture
async def client(app):
    """
    Async HTTP client that talks to the test app via ASGI transport.

    Uses ASGITransport so no real HTTP server is needed — requests go
    directly through the FastAPI/Starlette ASGI interface. This is
    faster and more reliable than spinning up a real server.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c
