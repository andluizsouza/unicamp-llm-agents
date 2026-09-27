"""Wrap LLM invoke and FAQ retrieve with retry + timeout when harness is on."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from recfair.harness.context import is_harness_enabled, llm_timeout_s, tool_timeout_s
from recfair.harness.retry import call_with_retry
from recfair.harness.timeout import run_with_timeout
from recfair.harness.unstable import maybe_fail


class HarnessStructuredLLM:
    """Proxy around LangChain structured-output runnable."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner

    def invoke(self, *args: Any, **kwargs: Any) -> Any:
        """Invoke the inner runnable, optionally with timeout and retry."""
        if not is_harness_enabled():
            return self._inner.invoke(*args, **kwargs)

        def _once() -> Any:
            return run_with_timeout(self._inner.invoke, llm_timeout_s(), *args, **kwargs)

        return call_with_retry(_once)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def wrap_structured_llm(inner: Any) -> HarnessStructuredLLM:
    """Always wrap; the proxy is a no-op unless the harness is enabled."""
    if isinstance(inner, HarnessStructuredLLM):
        return inner
    return HarnessStructuredLLM(inner)


def retrieve_with_harness(
    impl: Callable[..., list[dict[str, Any]]],
    query: str,
    *,
    k: int,
) -> list[dict[str, Any]]:
    """FAQ retrieve with injection, timeout and retry (harness on)."""

    def _once() -> list[dict[str, Any]]:
        maybe_fail()
        return run_with_timeout(impl, tool_timeout_s(), query, k=k)

    return call_with_retry(_once)
