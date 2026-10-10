"""
Phase 2 Tests — Health Endpoint

Tests for GET /health/

Covers:
1. Successful response shape and field types
2. DB connectivity status when DB is reachable
3. Response always returns HTTP 200 (even when DB is down, status='degraded')
4. Version and environment fields come from config, not hardcoded
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient) -> None:
    """Health endpoint must always return HTTP 200."""
    response = await client.get("/health/")
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Body: {response.text}"
    )


@pytest.mark.asyncio
async def test_health_response_schema(client: AsyncClient) -> None:
    """Response must contain all required fields with correct types."""
    response = await client.get("/health/")
    data = response.json()

    assert "status" in data, "Missing 'status' field"
    assert "version" in data, "Missing 'version' field"
    assert "db" in data, "Missing 'db' field"
    assert "environment" in data, "Missing 'environment' field"

    assert isinstance(data["status"], str)
    assert isinstance(data["version"], str)
    assert isinstance(data["db"], str)
    assert isinstance(data["environment"], str)

    # db_error is optional — must be str or None
    assert data.get("db_error") is None or isinstance(data["db_error"], str)


@pytest.mark.asyncio
async def test_health_status_values(client: AsyncClient) -> None:
    """
    'status' must be 'ok' or 'degraded'.
    'db' must be 'ok' or 'error'.
    """
    response = await client.get("/health/")
    data = response.json()

    assert data["status"] in ("ok", "degraded"), (
        f"Unexpected status value: {data['status']!r}"
    )
    assert data["db"] in ("ok", "error"), (
        f"Unexpected db value: {data['db']!r}"
    )


@pytest.mark.asyncio
async def test_health_version_matches_config(client: AsyncClient, settings) -> None:
    """Version in response must match the configured app version."""
    response = await client.get("/health/")
    data = response.json()

    assert data["version"] == settings.app_version, (
        f"Version mismatch: response={data['version']!r}, "
        f"config={settings.app_version!r}"
    )


@pytest.mark.asyncio
async def test_health_environment_matches_config(client: AsyncClient, settings) -> None:
    """Environment field must match app_env from config."""
    response = await client.get("/health/")
    data = response.json()

    assert data["environment"] == settings.app_env, (
        f"Environment mismatch: response={data['environment']!r}, "
        f"config={settings.app_env!r}"
    )


@pytest.mark.asyncio
async def test_health_db_ok_when_db_reachable(client: AsyncClient) -> None:
    """
    When the database is reachable, status should be 'ok' and db should be 'ok'.

    NOTE: This test requires the PostgreSQL container to be running.
    If PostgreSQL is not running, status='degraded' and db='error' are
    acceptable — the test will log a warning but not fail the suite.
    """
    response = await client.get("/health/")
    data = response.json()

    if data["db"] == "error":
        # Not a test failure — DB might not be up in CI.
        # The important thing is that the endpoint returned 200
        # and the schema is correct, which earlier tests verified.
        pytest.skip(
            "Database is not reachable in this environment. "
            f"db_error={data.get('db_error')!r}. "
            "Start PostgreSQL with: docker compose up -d db"
        )

    assert data["db"] == "ok"
    assert data["status"] == "ok"
    assert data["db_error"] is None


@pytest.mark.asyncio
async def test_health_content_type_is_json(client: AsyncClient) -> None:
    """Response Content-Type must be application/json."""
    response = await client.get("/health/")
    assert "application/json" in response.headers.get("content-type", ""), (
        f"Expected JSON content type, got: {response.headers.get('content-type')}"
    )
