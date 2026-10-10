"""
GeoMeasure Studio — Application Configuration

All settings are loaded from environment variables (or a .env file).
Never hardcode secrets. This module is the single source of truth for
all runtime configuration values used by the backend.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Pydantic BaseSettings reads values from environment variables first,
    then from a .env file if present. Type annotations act as validators.
    """

    model_config = SettingsConfigDict(
        # Look for a .env file in the backend directory at startup
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore unknown env vars gracefully
    )

    # ── Application ───────────────────────────────────────────────
    app_env: str = Field(default="development", description="Environment name")
    app_version: str = Field(default="0.1.0", description="Application version")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    debug: bool = Field(default=False)

    # ── Database ──────────────────────────────────────────────────
    # Async URL used by SQLAlchemy at runtime (asyncpg driver)
    database_url: str = Field(
        default="postgresql+asyncpg://geomeasure:geomeasure_dev@localhost:5432/geomeasure_db",
        description="PostgreSQL connection string with asyncpg driver",
    )
    # Sync URL used ONLY by Alembic migrations (psycopg2 driver)
    database_url_sync: str = Field(
        default="postgresql+psycopg2://geomeasure:geomeasure_dev@localhost:5432/geomeasure_db",
        description="PostgreSQL connection string with psycopg2 driver (Alembic only)",
    )

    # ── CORS ──────────────────────────────────────────────────────
    frontend_origins: list[str] | str = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins (comma-separated in env)",
    )

    @field_validator("frontend_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> list[str]:
        """Allow comma-separated string from env var or a Python list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return list(v)

    # ── File Upload ───────────────────────────────────────────────
    max_upload_size_mb: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum upload file size in megabytes",
    )
    max_zip_uncompressed_mb: int = Field(
        default=200,
        description="Maximum total uncompressed size of a ZIP archive (bomb protection)",
    )
    max_zip_entries: int = Field(
        default=1000,
        description="Maximum number of entries in a ZIP archive",
    )

    # ── Storage Paths ─────────────────────────────────────────────
    # These are relative to the backend directory
    upload_dir: str = Field(default="uploads")
    temp_dir: str = Field(default="tmp")

    # ── Logging ───────────────────────────────────────────────────
    log_level: str = Field(default="INFO")
    log_format: str = Field(
        default="json",
        description="'json' for structured production logs, 'console' for dev",
    )

    # ── Computed helpers (not from env) ───────────────────────────
    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def max_zip_uncompressed_bytes(self) -> int:
        return self.max_zip_uncompressed_mb * 1024 * 1024

    @property
    def backend_dir(self) -> Path:
        """Absolute path to the backend/ directory."""
        return Path(__file__).resolve().parents[2]

    @property
    def upload_path(self) -> Path:
        return self.backend_dir / self.upload_dir

    @property
    def temp_path(self) -> Path:
        return self.backend_dir / self.temp_dir

    def ensure_directories(self) -> None:
        """Create runtime directories if they don't exist."""
        self.upload_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings singleton.

    Using @lru_cache means environment variables are read once at startup,
    not on every request. Call get_settings.cache_clear() in tests to
    reset the cache between test runs.
    """
    return Settings()
