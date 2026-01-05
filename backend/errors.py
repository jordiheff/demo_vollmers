"""
Standardized error handling for the application.
Provides consistent error responses across all API endpoints.
"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel
from fastapi import Request, status
from fastapi.responses import JSONResponse


class ErrorCode(str, Enum):
    """Standardized error codes for the application."""

    # Validation errors (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_SERVING_SIZE = "INVALID_SERVING_SIZE"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"

    # Processing errors (422)
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    CALCULATION_FAILED = "CALCULATION_FAILED"
    LABEL_GENERATION_FAILED = "LABEL_GENERATION_FAILED"
    OCR_FAILED = "OCR_FAILED"
    PDF_PARSE_FAILED = "PDF_PARSE_FAILED"

    # External service errors (502)
    OPENAI_API_ERROR = "OPENAI_API_ERROR"
    USDA_API_ERROR = "USDA_API_ERROR"

    # Internal errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"


class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: Optional[str] = None
    message: str
    value: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    success: bool = False
    error_code: ErrorCode
    message: str
    details: Optional[list[ErrorDetail]] = None
    request_id: Optional[str] = None

    class Config:
        use_enum_values = True


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[list[ErrorDetail]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class ValidationException(AppException):
    """Exception for validation errors."""

    def __init__(self, message: str, details: Optional[list[ErrorDetail]] = None):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class ExtractionException(AppException):
    """Exception for extraction errors."""

    def __init__(self, message: str, details: Optional[list[ErrorDetail]] = None):
        super().__init__(
            error_code=ErrorCode.EXTRACTION_FAILED,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class ExternalServiceException(AppException):
    """Exception for external service errors (OpenAI, USDA)."""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[list[ErrorDetail]] = None
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )


def create_error_response(
    error_code: ErrorCode,
    message: str,
    details: Optional[list[ErrorDetail]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """
    Create a standardized error response.

    Args:
        error_code: The error code enum value
        message: Human-readable error message
        details: Optional list of detailed error information
        request_id: Optional request ID for tracing

    Returns:
        ErrorResponse model
    """
    return ErrorResponse(
        success=False,
        error_code=error_code,
        message=message,
        details=details,
        request_id=request_id
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    FastAPI exception handler for AppException.

    Args:
        request: The incoming request
        exc: The raised AppException

    Returns:
        JSONResponse with standardized error format
    """
    from logging_config import get_logger
    logger = get_logger("error_handler")

    logger.error("Application exception", data={
        "error_code": exc.error_code.value,
        "message": exc.message,
        "status_code": exc.status_code,
        "path": str(request.url.path)
    })

    response = create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    FastAPI exception handler for unhandled exceptions.

    Args:
        request: The incoming request
        exc: The raised exception

    Returns:
        JSONResponse with standardized error format
    """
    from logging_config import get_logger
    logger = get_logger("error_handler")

    logger.exception("Unhandled exception", data={
        "exception_type": type(exc).__name__,
        "message": str(exc),
        "path": str(request.url.path)
    })

    response = create_error_response(
        error_code=ErrorCode.INTERNAL_ERROR,
        message="An unexpected error occurred. Please try again later."
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump()
    )


# Convenience functions for common errors

def validation_error(message: str, field: Optional[str] = None, value: Any = None) -> ErrorResponse:
    """Create a validation error response."""
    details = None
    if field:
        details = [ErrorDetail(field=field, message=message, value=value)]
    return create_error_response(ErrorCode.VALIDATION_ERROR, message, details)


def extraction_error(message: str) -> ErrorResponse:
    """Create an extraction error response."""
    return create_error_response(ErrorCode.EXTRACTION_FAILED, message)


def openai_error(message: str) -> ErrorResponse:
    """Create an OpenAI API error response."""
    return create_error_response(ErrorCode.OPENAI_API_ERROR, message)


def file_type_error(filename: str, allowed_types: list[str]) -> ErrorResponse:
    """Create an invalid file type error response."""
    return create_error_response(
        ErrorCode.INVALID_FILE_TYPE,
        f"Invalid file type for '{filename}'. Allowed types: {', '.join(allowed_types)}",
        details=[ErrorDetail(
            field="file_type",
            message=f"Allowed types: {', '.join(allowed_types)}",
            value=filename
        )]
    )
