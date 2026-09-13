"""Map architecture_id to runnable implementations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from recfair.config import CURRENT_ARCH, resolve_arch
from recfair.graphs import baseline

RunnerFn = Callable[[str], tuple[Any, Any]]

_ARCHITECTURES: dict[str, RunnerFn] = {
    "baseline": baseline.run,
}


def resolve_architecture(arch: str | None) -> str:
    """Resolve CLI arch flag to a registered architecture id."""
    resolved = resolve_arch(arch)
    if resolved not in _ARCHITECTURES:
        known = ", ".join(sorted(_ARCHITECTURES))
        raise ValueError(
            f"Unknown architecture '{resolved}'. Known: {known}, current={CURRENT_ARCH}"
        )
    return resolved


def get_runner(arch: str | None) -> tuple[str, RunnerFn]:
    """Return (architecture_id, run callable)."""
    arch_id = resolve_architecture(arch)
    return arch_id, _ARCHITECTURES[arch_id]


def list_architectures() -> list[str]:
    """Registered architecture ids."""
    return sorted(_ARCHITECTURES)
