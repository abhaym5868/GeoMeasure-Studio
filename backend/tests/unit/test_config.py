"""
Phase 2 Tests — Configuration

Tests that the Pydantic Settings class correctly reads, validates,
and provides configuration values.
"""
from __future__ import annotations

from app.core.config import Settings, get_settings


def test_settings_singleton() -> None:
    """get_settings() must return the same object on repeated calls."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2, "Settings should be a cached singleton"


def test_settings_has_database_url() -> None:
    """DATABASE_URL must be set and start with the asyncpg driver prefix."""
    settings = get_settings()
    assert settings.database_url, "database_url must not be empty"
    assert settings.database_url.startswith("postgresql+asyncpg://"), (
        f"database_url must use asyncpg driver, got: {settings.database_url[:40]}"
    )


def test_settings_has_sync_database_url() -> None:
    """DATABASE_URL_SYNC must use psycopg2 driver for Alembic."""
    settings = get_settings()
    assert settings.database_url_sync, "database_url_sync must not be empty"
    assert settings.database_url_sync.startswith("postgresql+psycopg2://"), (
        f"database_url_sync must use psycopg2 driver, got: {settings.database_url_sync[:40]}"
    )


def test_max_upload_size_bytes_computed_correctly() -> None:
    """Computed byte limit must be exactly MB * 1024 * 1024."""
    settings = get_settings()
    expected = settings.max_upload_size_mb * 1024 * 1024
    assert settings.max_upload_size_bytes == expected


def test_frontend_origins_is_list() -> None:
    """frontend_origins must be a non-empty list of strings."""
    settings = get_settings()
    assert isinstance(settings.frontend_origins, list)
    assert len(settings.frontend_origins) > 0
    for origin in settings.frontend_origins:
        assert isinstance(origin, str)


def test_origins_validator_parses_comma_string() -> None:
    """The parse_origins validator must split a comma-separated string."""
    s = Settings(
        database_url="postgresql+asyncpg://u:p@localhost/db",
        database_url_sync="postgresql+psycopg2://u:p@localhost/db",
        frontend_origins="http://a.com, http://b.com",
    )
    assert s.frontend_origins == ["http://a.com", "http://b.com"]


def test_upload_path_is_absolute() -> None:
    """upload_path must be an absolute Path."""
    settings = get_settings()
    assert settings.upload_path.is_absolute()


def test_temp_path_is_absolute() -> None:
    """temp_path must be an absolute Path."""
    settings = get_settings()
    assert settings.temp_path.is_absolute()
