"""
GeoMeasure Studio — SQLAlchemy Declarative Base

All ORM models inherit from this Base. Using a single shared Base
ensures all models share the same MetaData instance, which is required
for Alembic's autogenerate to discover all tables in one place.
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Project-wide SQLAlchemy declarative base.

    SQLAlchemy 2.x style: models use Mapped[] type annotations instead
    of Column() assignments. This gives IDE type inference and runtime
    type validation from the ORM layer.
    """
    pass
