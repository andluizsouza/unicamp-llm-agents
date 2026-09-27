"""Per-operation timeout using a daemon worker thread."""

from __future__ import annotations

import threading
from collections.abc import Callable
from contextvars import copy_context


class TimeoutExpired(TimeoutError):
    """Operation exceeded its allotted time."""


def run_with_timeout[T](
    fn: Callable[..., T],
    timeout_s: float,
    *args: object,
    **kwargs: object,
) -> T:
    """Run ``fn(*args, **kwargs)`` and raise if it exceeds ``timeout_s``.

    The worker is a daemon thread so a timeout unblocks the caller immediately.
    The worker is not killed (Python cannot stop a running thread). ContextVars
    from the caller are copied into the worker.

    Args:
        fn: Callable to execute.
        timeout_s: Deadline in seconds.
        *args: Positional arguments for ``fn``.
        **kwargs: Keyword arguments for ``fn``.

    Returns:
        The return value of ``fn``.

    Raises:
        TimeoutExpired: The deadline elapsed.
    """
    if timeout_s <= 0:
        raise TimeoutExpired("timeout_s must be positive")

    ctx = copy_context()
    box: dict[str, T] = {}
    errors: list[BaseException] = []

    def _worker() -> None:
        try:
            box["value"] = ctx.run(fn, *args, **kwargs)
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=_worker, name="recfair-timeout", daemon=True)
    thread.start()
    thread.join(timeout=timeout_s)
    if thread.is_alive():
        raise TimeoutExpired(f"operation exceeded {timeout_s:.1f}s")
    if errors:
        raise errors[0]
    return box["value"]
