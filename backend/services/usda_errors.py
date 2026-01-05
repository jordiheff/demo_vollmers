"""
USDA API error handling.
"""

from enum import Enum
from typing import Optional


class USDAErrorType(str, Enum):
    """Types of errors from USDA API."""
    RATE_LIMITED = "rate_limited"
    NOT_FOUND = "not_found"
    INVALID_KEY = "invalid_key"
    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"


class USDAAPIError(Exception):
    """Exception for USDA API errors."""

    def __init__(
        self,
        error_type: USDAErrorType,
        message: str,
        status_code: Optional[int] = None,
        retry_after: Optional[int] = None
    ):
        self.error_type = error_type
        self.message = message
        self.status_code = status_code
        self.retry_after = retry_after
        super().__init__(message)


def handle_usda_response(response) -> dict:
    """
    Handle USDA API response and raise appropriate errors.

    Args:
        response: httpx Response object

    Returns:
        Parsed JSON response

    Raises:
        USDAAPIError: On any non-success response
    """
    if response.status_code == 200:
        return response.json()

    if response.status_code == 400:
        raise USDAAPIError(
            USDAErrorType.INVALID_KEY,
            "Invalid API key or malformed request",
            status_code=400
        )

    if response.status_code == 404:
        raise USDAAPIError(
            USDAErrorType.NOT_FOUND,
            "Food item not found in USDA database",
            status_code=404
        )

    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        raise USDAAPIError(
            USDAErrorType.RATE_LIMITED,
            f"Rate limited. Retry after {retry_after} seconds.",
            status_code=429,
            retry_after=retry_after
        )

    if response.status_code >= 500:
        raise USDAAPIError(
            USDAErrorType.SERVER_ERROR,
            f"USDA API server error: {response.status_code}",
            status_code=response.status_code
        )

    raise USDAAPIError(
        USDAErrorType.SERVER_ERROR,
        f"Unexpected response: {response.status_code}",
        status_code=response.status_code
    )
