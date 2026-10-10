"""
GeoMeasure Studio — DB package.

This module is imported by Alembic's env.py to ensure all ORM models
are registered with the metadata before migrations are generated.
Import every model here even if not directly used.
"""
from app.models.base import Base  # noqa: F401

# Phase 6 will add:
# from app.models.file_record import FileRecord  # noqa: F401
# from app.models.feature_record import FeatureRecord  # noqa: F401

__all__ = ["Base"]
