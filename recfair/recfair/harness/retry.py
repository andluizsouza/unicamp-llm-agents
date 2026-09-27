"""Retry with exponential backoff, only for transient failures."""

from __future__ import annotations

import random
import time
from collections.abc import Callable

from recfair.harness.context import base_backoff_s, max_retries
from recfair.harness.timeout import TimeoutExpired

_TRANSIENT_TYPES = {
    "TimeoutError",
    "TimeoutExpired",
    "ConnectionError",
    "ConnectionResetError",
    "BrokenPipeError",
    "OSError",
    "FonteIndisponivel",
}

_TRANSIENT_MARKERS = (
    "timeout",
    "timed out",
    "temporarily unavailable",
    "unavailable",
    "429",
    "503",
    "504",
    "rate limit",
    "resource exhausted",
    "deadline exceeded",
    "service unavailable",
    "connection reset",
    "fonte faq instável",
    "fonte faq instavel",
)


class TransientError(Exception):
    """Raised when retries are exhausted on a transient failure."""


def is_transient(exc: BaseException) -> bool:
    """Return True if ``exc`` looks like a retryable infrastructure failure."""
    name = type(exc).__name__
    if name in _TRANSIENT_TYPES:
        return True
    text = f"{name}: {exc}".lower()
    return any(marker in text for marker in _TRANSIENT_MARKERS)


def call_with_retry[T](
    fn: Callable[[], T],
    *,
    attempts: int | None = None,
    backoff_s: float | None = None,
    sleep: Callable[[float], None] = time.sleep,
    jitter: bool = True,
) -> T:
    """Call ``fn`` until it succeeds or the retry budget is spent.

    Persistent errors (bad arguments, assertion failures) are not retried.

    Args:
        fn: Zero-argument callable.
        attempts: Max tries including the first. Defaults to harness settings.
        backoff_s: Base wait in seconds before the second try.
        sleep: Injected sleeper (tests pass a no-op).
        jitter: Add a small random delay so concurrent retries do not stampede.

    Returns:
        The successful return value of ``fn``.

    Raises:
        TransientError: All attempts failed with transient errors.
        BaseException: The last non-transient error, re-raised as-is.
    """
    n = max_retries() + 1 if attempts is None else max(1, attempts)
    wait = base_backoff_s() if backoff_s is None else backoff_s
    last_transient: BaseException | None = None
    for index in range(n):
        try:
            return fn()
        except BaseException as exc:
            if not is_transient(exc):
                raise
            last_transient = exc
            if index >= n - 1:
                break
            delay = wait * (2**index)
            if jitter:
                delay += random.uniform(0, wait * 0.25)
            sleep(delay)
    assert last_transient is not None
    if isinstance(last_transient, TimeoutExpired):
        raise last_transient
    name = type(last_transient).__name__
    raise TransientError(f"retries exhausted: {name}: {last_transient}") from last_transient
