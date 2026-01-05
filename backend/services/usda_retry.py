"""
Retry logic with exponential backoff for USDA API.
"""

import asyncio
from typing import TypeVar, Callable
from functools import wraps
from .usda_errors import USDAAPIError, USDAErrorType

T = TypeVar("T")


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_errors: tuple = (
        USDAErrorType.TIMEOUT,
        USDAErrorType.SERVER_ERROR,
        USDAErrorType.NETWORK_ERROR,
    )
):
    """
    Decorator for retrying USDA API calls with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        retryable_errors: Error types that should trigger retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except USDAAPIError as e:
                    last_error = e

                    # Don't retry non-retryable errors
                    if e.error_type not in retryable_errors:
                        raise

                    # Don't retry on last attempt
                    if attempt == max_attempts - 1:
                        raise

                    # Calculate delay with exponential backoff
                    if e.error_type == USDAErrorType.RATE_LIMITED and e.retry_after:
                        delay = e.retry_after
                    else:
                        delay = min(base_delay * (2 ** attempt), max_delay)

                    await asyncio.sleep(delay)

            raise last_error

        return wrapper
    return decorator
