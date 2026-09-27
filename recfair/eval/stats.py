"""Binomial confidence intervals for small evaluation sets (E4 §4.1)."""

from __future__ import annotations

import math


def intervalo_wilson(
    acertos: int,
    total: int,
    z: float = 1.96,
) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Args:
        acertos: Number of successes.
        total: Number of trials.
        z: Normal quantile (1.96 ≈ 95%).

    Returns:
        ``(low, high)`` clipped to ``[0, 1]``. Empty total yields ``(0, 1)``.
    """
    if total <= 0:
        return (0.0, 1.0)
    acertos = max(0, min(int(acertos), int(total)))
    p = acertos / total
    z2 = z * z
    denom = 1.0 + z2 / total
    center = (p + z2 / (2.0 * total)) / denom
    margin = (z / denom) * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return (max(0.0, center - margin), min(1.0, center + margin))


def sobrepoe(left: tuple[float, float], right: tuple[float, float]) -> bool:
    """Return True when two closed intervals overlap (including a shared endpoint)."""
    return left[0] <= right[1] and right[0] <= left[1]
