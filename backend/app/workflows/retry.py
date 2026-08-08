"""Custom async retry infrastructure replacing Temporal RetryPolicy.

Provides an @async_retry decorator with per-activity retry configuration:
  - max_attempts: maximum retry count
  - initial_interval: seconds before first retry
  - backoff_coefficient: multiplier for each subsequent retry
  - non_retryable_errors: exception types that fail immediately (no retries)
  - timeout: overall timeout per invocation (replaces start_to_close_timeout)
"""

from __future__ import annotations

import asyncio
import functools
from typing import Any, Callable, TypeVar

from app.core.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def async_retry(
    *,
    max_attempts: int = 3,
    initial_interval: float = 1.0,
    backoff_coefficient: float = 2.0,
    non_retryable_errors: list[type] | None = None,
    timeout: float | None = None,
) -> Callable[[F], F]:
    """Decorator providing configurable async retry with exponential backoff.

    Mirrors Temporal's RetryPolicy semantics:
      - Retries up to max_attempts on transient failures.
      - Fails immediately (no retry) for exceptions in non_retryable_errors.
      - Applies exponential backoff: delay = initial_interval * (backoff_coefficient ** attempt).
      - Optional overall timeout wrapping each invocation.
    """
    _non_retryable = tuple(non_retryable_errors or [])

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    if timeout is not None:
                        return await asyncio.wait_for(
                            func(*args, **kwargs), timeout=timeout
                        )
                    return await func(*args, **kwargs)

                except _non_retryable as exc:
                    # Non-retryable error — fail immediately without wasting retries
                    logger.warning(
                        f"{func.__name__}: non-retryable error on attempt {attempt}/{max_attempts}: {exc}",
                        extra={"activity": func.__name__, "attempt": attempt, "retryable": False},
                    )
                    raise

                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__}: all {max_attempts} attempts exhausted: {exc}",
                            extra={"activity": func.__name__, "attempt": attempt},
                        )
                        raise

                    delay = initial_interval * (backoff_coefficient ** (attempt - 1))
                    logger.info(
                        f"{func.__name__}: attempt {attempt}/{max_attempts} failed, retrying in {delay:.1f}s: {exc}",
                        extra={"activity": func.__name__, "attempt": attempt, "delay": delay},
                    )
                    await asyncio.sleep(delay)

            # Should not reach here, but just in case
            if last_exc is not None:
                raise last_exc
            raise RuntimeError(f"{func.__name__}: retry loop exited unexpectedly")

        return wrapper  # type: ignore[return-value]

    return decorator
