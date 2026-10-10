"""
GeoMeasure Studio — Custom Exceptions and FastAPI Error Handlers

Design principles:
- Each domain error has a dedicated exception class with a machine-readable
  'code' and a safe, user-facing 'detail' message.
- Internal details (file paths, stack traces, SQL errors) are NEVER
  exposed in API responses — they are logged server-side.
- All handlers return a consistent JSON shape so the frontend can
  reliably parse and display errors.

Error response format:
    {
        "detail": "Human-readable message safe for display",
        "code": "MACHINE_CODE",
        "field": "optional_field_name"   // only for validation errors
    }
"""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

# ─────────────────────────────────────────────────────────────────
# Base exception
# ─────────────────────────────────────────────────────────────────

class GeoMeasureError(Exception):
    """Base for all application-level exceptions."""

    def __init__(
        self,
        detail: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        field: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.code = code
        self.status_code = status_code
        self.field = field


# ─────────────────────────────────────────────────────────────────
# File / upload exceptions
# ─────────────────────────────────────────────────────────────────

class FileValidationError(GeoMeasureError):
    """Raised when an uploaded file fails format or content validation."""

    def __init__(self, detail: str, code: str = "FILE_VALIDATION_ERROR", field: str | None = None) -> None:
        super().__init__(
            detail=detail,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
            field=field,
        )


class FileTooLargeError(FileValidationError):
    def __init__(self, size_mb: float, limit_mb: int) -> None:
        super().__init__(
            detail=f"File size {size_mb:.1f} MB exceeds the {limit_mb} MB limit.",
            code="FILE_TOO_LARGE",
        )


class UnsupportedFileTypeError(FileValidationError):
    def __init__(self, extension: str) -> None:
        super().__init__(
            detail=f"File type '{extension}' is not supported. Upload a .kml or .zip file.",
            code="UNSUPPORTED_FILE_TYPE",
        )


class InvalidFileContentError(FileValidationError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, code="INVALID_FILE_CONTENT")


class ZipSafetyError(FileValidationError):
    """Raised when a ZIP archive fails security checks."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, code="ZIP_SAFETY_ERROR")


# ─────────────────────────────────────────────────────────────────
# Geospatial / processing exceptions
# ─────────────────────────────────────────────────────────────────

class GeospatialReadError(GeoMeasureError):
    """Raised when a geospatial file cannot be parsed."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            code="GEOSPATIAL_READ_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class CRSError(GeoMeasureError):
    """Raised when CRS cannot be determined and no fallback is safe."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            code="CRS_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class ProcessingError(GeoMeasureError):
    """General processing failure after validation passed."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            code="PROCESSING_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ─────────────────────────────────────────────────────────────────
# Resource exceptions
# ─────────────────────────────────────────────────────────────────

class FileNotFoundError(GeoMeasureError):
    def __init__(self, file_id: str) -> None:
        super().__init__(
            detail=f"File with ID '{file_id}' was not found.",
            code="FILE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ExportError(GeoMeasureError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            code="EXPORT_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


# ─────────────────────────────────────────────────────────────────
# FastAPI exception handlers
# ─────────────────────────────────────────────────────────────────

def _error_response(detail: str, code: str, field: str | None = None, status_code: int = 500) -> JSONResponse:
    body: dict = {"detail": detail, "code": code}
    if field is not None:
        body["field"] = field
    return JSONResponse(status_code=status_code, content=body)


async def geomeasure_exception_handler(request: Request, exc: GeoMeasureError) -> JSONResponse:
    """Converts any GeoMeasureError into a structured JSON response."""
    return _error_response(
        detail=exc.detail,
        code=exc.code,
        field=exc.field,
        status_code=exc.status_code,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for unexpected errors.
    IMPORTANT: never expose exc details to the client — log them instead.
    """
    from app.core.logging import get_logger  # avoid circular import

    logger = get_logger(__name__)
    logger.error(
        "Unhandled exception",
        path=str(request.url),
        method=request.method,
        exc_info=True,
    )
    return _error_response(
        detail="An unexpected error occurred. Please try again or contact support.",
        code="INTERNAL_SERVER_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app instance."""
    app.add_exception_handler(GeoMeasureError, geomeasure_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]
