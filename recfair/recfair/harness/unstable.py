"""Optional unstable FAQ source (Atividade Prática 7, p=0.4 demo)."""

from __future__ import annotations

import random

from recfair.harness.context import inject_failure_prob


class FonteIndisponivel(RuntimeError):
    """Transient FAQ source failure. Retryable; not a logic bug."""


def maybe_fail(*, rng: random.Random | None = None) -> None:
    """Raise ``FonteIndisponivel`` with the configured injection probability.

    Args:
        rng: Optional RNG for deterministic demos. Uses ``random`` when omitted.

    No-op when the probability is 0 (production default).
    """
    prob = inject_failure_prob()
    if prob <= 0:
        return
    draw = (rng or random).random()
    if draw < prob:
        raise FonteIndisponivel(f"fonte FAQ instável (injeção p={prob})")
