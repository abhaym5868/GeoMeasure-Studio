"""
GeoMeasure Studio — Common Pydantic Schemas

Shared response types used across multiple API endpoints.
"""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated list response.

    All list endpoints return this wrapper so the frontend always has
    consistent metadata for building pagination controls.
    """

    items: list[T]
    total: int = Field(description="Total number of matching records")
    page: int = Field(description="Current page number (1-indexed)")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[T]:
        total_pages = max(1, (total + page_size - 1) // page_size)
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class ErrorResponse(BaseModel):
    """Standard error envelope returned by all exception handlers."""

    detail: str = Field(description="Human-readable error message")
    code: str = Field(description="Machine-readable error code")
    field: str | None = Field(default=None, description="Field that caused the error")


class HealthStatus(BaseModel):
    """Response schema for GET /health/"""

    status: str = Field(description="Overall application status: 'ok' or 'degraded'")
    version: str = Field(description="Application version from config")
    db: str = Field(description="Database connectivity: 'ok' or 'error'")
    db_error: str | None = Field(
        default=None,
        description="Safe database error description (no internal paths or credentials)",
    )
    environment: str = Field(description="Deployment environment name")
