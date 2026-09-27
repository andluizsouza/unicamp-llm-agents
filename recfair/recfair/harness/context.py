"""ContextVar + env flags for the E4 harness (off by default)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, replace


def _env_float(name: str, default: float) -> float:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class HarnessSettings:
    """Per-invocation harness knobs. Defaults preserve E3 behaviour."""

    enabled: bool = False
    inject_failure_prob: float = 0.0
    llm_timeout_s: float = 45.0
    tool_timeout_s: float = 20.0
    max_retries: int = 3
    base_backoff_s: float = 0.4
    high_confidence: float = 0.8


def settings_from_env(*, enabled: bool = True) -> HarnessSettings:
    """Build settings, overlaying optional ``RECFAIR_*`` environment variables."""
    return HarnessSettings(
        enabled=enabled,
        inject_failure_prob=max(0.0, min(1.0, _env_float("RECFAIR_INJECT_FAILURE_PROB", 0.0))),
        llm_timeout_s=max(1.0, _env_float("RECFAIR_LLM_TIMEOUT_S", 45.0)),
        tool_timeout_s=max(1.0, _env_float("RECFAIR_TOOL_TIMEOUT_S", 20.0)),
        max_retries=max(0, _env_int("RECFAIR_MAX_RETRIES", 3)),
        base_backoff_s=max(0.0, _env_float("RECFAIR_BASE_BACKOFF_S", 0.4)),
    )


_SETTINGS: ContextVar[HarnessSettings] = ContextVar(
    "recfair_harness_settings",
    default=HarnessSettings(),
)


def current_settings() -> HarnessSettings:
    """Return the active harness settings for this task."""
    return _SETTINGS.get()


def is_harness_enabled() -> bool:
    """Whether the resilient harness is active on this call stack."""
    return current_settings().enabled


def inject_failure_prob() -> float:
    """Probability of an injected FAQ source failure (AP7 demo)."""
    return current_settings().inject_failure_prob


def llm_timeout_s() -> float:
    """Deadline in seconds for a single structured-LLM invoke."""
    return current_settings().llm_timeout_s


def tool_timeout_s() -> float:
    """Deadline in seconds for a single FAQ retrieve."""
    return current_settings().tool_timeout_s


def max_retries() -> int:
    """Extra attempts after the first try (total tries = this + 1)."""
    return current_settings().max_retries


def base_backoff_s() -> float:
    """Base wait in seconds before the second try."""
    return current_settings().base_backoff_s


@contextmanager
def harness_scope(settings: HarnessSettings | None = None) -> Iterator[HarnessSettings]:
    """Enable the harness for the duration of the block.

    Args:
        settings: Explicit settings. When omitted, loads from the environment
            with ``enabled=True``.

    Yields:
        The settings token that is now active.
    """
    active = settings if settings is not None else settings_from_env(enabled=True)
    token: Token[HarnessSettings] = _SETTINGS.set(active)
    try:
        yield active
    finally:
        _SETTINGS.reset(token)


def overlay_settings(**changes: object) -> HarnessSettings:
    """Return a copy of the current settings with selected fields replaced."""
    return replace(current_settings(), **changes)  # type: ignore[arg-type]
