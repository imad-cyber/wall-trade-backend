"""
Utility decorators — timing and retry with tenacity integration.
"""
from functools import wraps
from typing import Any, Callable

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.logging import get_logger

logger = get_logger(__name__)


def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time."""
    import time

    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            return await func(*args, **kwargs)
        finally:
            elapsed_time = time.time() - start_time
            logger.info("Function %s executed in %.2fs", func.__name__, elapsed_time)

    @wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed_time = time.time() - start_time
            logger.info("Function %s executed in %.2fs", func.__name__, elapsed_time)

    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def retry_decorator(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
) -> Callable:
    """Decorator using tenacity for retries with exponential backoff."""

    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=delay, min=delay, max=delay * backoff ** max_attempts),
            reraise=True,
        )
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            return await func(*args, **kwargs)

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=delay, min=delay, max=delay * backoff ** max_attempts),
            reraise=True,
        )
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            return func(*args, **kwargs)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
