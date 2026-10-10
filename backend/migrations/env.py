"""
Alembic Environment Configuration

This file is loaded by `alembic upgrade head` and `alembic revision --autogenerate`.
It bridges Alembic with our SQLAlchemy models and reads the database URL from
environment variables (never from alembic.ini directly, which would risk
committing credentials).

Key points:
- Reads DATABASE_URL_SYNC from environment (psycopg2 / sync driver).
- Imports app.db.base to register all ORM models with SQLAlchemy metadata
  so autogenerate can detect schema changes.
- Runs in 'online' mode only (we don't generate offline SQL scripts).
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Make sure the backend app package is importable ───────────────
# When alembic is run from backend/, `app` is on the path.
# Add the backend directory to sys.path to be safe.
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

# ── Import models and settings so Alembic sees all tables and config ─────
from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402  — must be after sys.path tweak
import app.db.base  # noqa: F401 — ensures all model imports in base.py run

# ── Alembic config object ─────────────────────────────────────────
config = context.config

# Configure Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Read DB URL from application settings (loads .env automatically) ─
# This is the SYNC url (psycopg2 driver). Alembic does not support asyncpg.
settings = get_settings()
db_url = settings.database_url_sync
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

target_metadata = Base.metadata


def run_migrations_online() -> None:
    """
    Run migrations with an actual database connection.

    'Online' mode applies migrations directly to the database.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Don't pool connections during migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,         # Detect column type changes
            compare_server_default=True,  # Detect default value changes
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
