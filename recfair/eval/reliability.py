"""Repeated golden-set runs and unstable-case detection (E4 §3.3)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from eval.cases import is_frozen_ruler_case
from eval.runner import run_eval


def _approved(record: dict[str, Any]) -> bool:
    return bool((record.get("check") or {}).get("aprovado"))


def filter_frozen_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep T01–T60 records for the inherited comparison ruler."""
    return [row for row in records if is_frozen_ruler_case(row.get("case") or {})]


def summarize_reliability(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate pass rates, min–max band, and cases that flip between runs.

    Args:
        manifests: Outputs of ``run_eval`` (same arch, same case list).

    Returns:
        Dict with per-run rates, band, and unstable case ids.
    """
    per_run: list[dict[str, Any]] = []
    flips: dict[str, list[bool]] = defaultdict(list)
    for index, manifest in enumerate(manifests, start=1):
        frozen = filter_frozen_records(list(manifest.get("records") or []))
        total = len(frozen)
        acertos = sum(1 for row in frozen if _approved(row))
        taxa = round(acertos / total, 4) if total else None
        per_run.append(
            {
                "rodada": index,
                "run_id": manifest.get("run_id"),
                "acertos": acertos,
                "total": total,
                "taxa": taxa,
            }
        )
        for row in frozen:
            case_id = str((row.get("case") or {}).get("id") or "")
            flips[case_id].append(_approved(row))

    taxas = [row["taxa"] for row in per_run if row["taxa"] is not None]
    instaveis = sorted(case_id for case_id, bits in flips.items() if bits and len(set(bits)) > 1)
    return {
        "n_rodadas": len(manifests),
        "por_rodada": per_run,
        "taxa_min": min(taxas) if taxas else None,
        "taxa_max": max(taxas) if taxas else None,
        "faixa": (min(taxas), max(taxas)) if taxas else None,
        "instaveis": instaveis,
        "architecture_id": manifests[0].get("architecture_id") if manifests else None,
        "model": manifests[0].get("model") if manifests else None,
        "golden_revision": manifests[0].get("golden_revision") if manifests else None,
    }


def run_reliability(
    arch: str | None = "resilient",
    n: int = 3,
    *,
    persist: bool = True,
    cases: list[dict[str, Any]] | None = None,
    fast_mode: bool = False,
) -> dict[str, Any]:
    """Execute ``run_eval`` ``n`` times and summarize variation.

    Args:
        arch: Architecture id.
        n: Number of repetitions (E4 requires ≥ 3 on the final version).
        persist: Forwarded to ``run_eval``.
        cases: Optional case subset.
        fast_mode: Forwarded to ``run_eval``.

    Returns:
        ``{"manifests": [...], "resumo": summarize_reliability(...)}``.
    """
    if n < 1:
        raise ValueError("n must be ≥ 1")
    manifests = [
        run_eval(arch, persist=persist, cases=cases, fast_mode=fast_mode) for _ in range(n)
    ]
    return {"manifests": manifests, "resumo": summarize_reliability(manifests)}
