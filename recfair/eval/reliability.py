"""Repeated golden-set runs and unstable-case detection (E4 §3.3)."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from eval.cases import is_frozen_ruler_case, load_cases
from eval.fingerprint import golden_revision
from eval.runner import run_eval
from recfair.config import eval_runs_dir

RELIABILITY_FULL_N = 3
_RELIABILITY_FULL_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "e4_reliability_full.json"


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


def _load_manifest(run_id: str) -> dict[str, Any] | None:
    path = eval_runs_dir() / f"{run_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _frozen_count(manifest: dict[str, Any]) -> int:
    return len(filter_frozen_records(list(manifest.get("records") or [])))


def _is_full_resilient_manifest(manifest: dict[str, Any], *, expected_revision: str | None) -> bool:
    if manifest.get("architecture_id") != "resilient":
        return False
    if manifest.get("fast_mode"):
        return False
    if _frozen_count(manifest) != 60:
        return False
    if expected_revision and manifest.get("golden_revision") != expected_revision:
        return False
    return True


def load_reliability_full_fixture() -> dict[str, Any] | None:
    """Pinned trio of full golden-set runs (written on first successful batch)."""
    if not _RELIABILITY_FULL_FIXTURE.is_file():
        return None
    return json.loads(_RELIABILITY_FULL_FIXTURE.read_text(encoding="utf-8"))


def save_reliability_full_fixture(run_ids: list[str], *, revision: str) -> Path:
    """Persist the three run ids used for full-mode reliability."""
    _RELIABILITY_FULL_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"golden_revision": revision, "run_ids": run_ids}
    _RELIABILITY_FULL_FIXTURE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return _RELIABILITY_FULL_FIXTURE


def list_full_resilient_run_ids(
    *,
    revision: str | None = None,
    limit: int = RELIABILITY_FULL_N,
) -> list[str]:
    """Most recent full ``resilient`` manifests (60× frozen), newest first."""
    revision = revision or golden_revision(load_cases())
    candidates: list[tuple[str, str]] = []
    for path in eval_runs_dir().glob("*.json"):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not _is_full_resilient_manifest(manifest, expected_revision=revision):
            continue
        run_id = str(manifest.get("run_id") or path.stem)
        started = str(manifest.get("started_at") or "")
        candidates.append((started, run_id))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return [run_id for _, run_id in candidates[:limit]]


def reliability_rates_frame(manifests: list[dict[str, Any]]) -> pd.DataFrame:
    """One row per repetition with pass rate (comparative table for §D)."""
    resumo = summarize_reliability(manifests)
    rows: list[dict[str, Any]] = []
    for row in resumo["por_rodada"]:
        taxa = row.get("taxa")
        rows.append(
            {
                "rodada": row.get("rodada"),
                "run_id": row.get("run_id"),
                "acertos": row.get("acertos"),
                "total": row.get("total"),
                "taxa": taxa,
                "taxa_%": round(float(taxa) * 100, 2) if taxa is not None else None,
            }
        )
    frame = pd.DataFrame(rows)
    if resumo.get("faixa"):
        lo, hi = resumo["faixa"]
        frame.attrs["faixa_min"] = lo
        frame.attrs["faixa_max"] = hi
    return frame


def reliability_variation_frame(manifests: list[dict[str, Any]]) -> pd.DataFrame:
    """Cases whose ``aprovado`` flag differs across repetitions."""
    if not manifests:
        return pd.DataFrame(columns=["caso"])
    by_case: dict[str, dict[str, Any]] = {}
    for index, manifest in enumerate(manifests, start=1):
        label = f"rodada_{index}"
        run_id = manifest.get("run_id")
        for row in filter_frozen_records(list(manifest.get("records") or [])):
            case_id = str((row.get("case") or {}).get("id") or "")
            bucket = by_case.setdefault(case_id, {"caso": case_id})
            approved = _approved(row)
            bucket[label] = "sucesso" if approved else "erro"
            bucket[f"{label}_run_id"] = run_id
    varying: list[dict[str, Any]] = []
    for bucket in by_case.values():
        flags = [bucket.get(f"rodada_{i}") for i in range(1, len(manifests) + 1)]
        if len(set(flags)) > 1:
            varying.append({key: bucket[key] for key in ("caso",) + tuple(f"rodada_{i}" for i in range(1, len(manifests) + 1))})
    if not varying:
        return pd.DataFrame(columns=["caso"] + [f"rodada_{i}" for i in range(1, len(manifests) + 1)])
    cols = ["caso"] + [f"rodada_{i}" for i in range(1, len(manifests) + 1)]
    return pd.DataFrame(sorted(varying, key=lambda r: r["caso"]))[cols]


def ensure_e4_reliability(
    *,
    fast_mode: bool,
    cases: list[dict[str, Any]] | None = None,
    n: int = RELIABILITY_FULL_N,
    arch: str = "resilient",
) -> dict[str, Any]:
    """Load or execute ``n`` repetitions of E4 for section D.

    Fast mode: always runs ``n`` times (non-persisted) on the given case subset.

    Full mode: reuses the trio in ``eval/fixtures/e4_reliability_full.json`` when
    valid; otherwise loads the latest ``n`` full manifests on disk; only if fewer
    than ``n`` exist, runs the missing repetitions (persisted) and writes the fixture
    on the first complete batch.

    Returns:
        Dict with ``manifests``, ``resumo``, ``rates_df``, ``variation_df``, and
        ``source`` (``fixture`` | ``disk`` | ``executed`` | ``executed_partial``).
    """
    if n < 1:
        raise ValueError("n must be ≥ 1")
    all_cases = load_cases()
    revision = golden_revision(all_cases)
    case_list = cases if cases is not None else all_cases

    if fast_mode:
        manifests = [
            run_eval(arch, persist=False, cases=case_list, fast_mode=True) for _ in range(n)
        ]
        resumo = summarize_reliability(manifests)
        return {
            "manifests": manifests,
            "resumo": resumo,
            "rates_df": reliability_rates_frame(manifests),
            "variation_df": reliability_variation_frame(manifests),
            "source": "executed",
            "fast_mode": True,
        }

    manifests: list[dict[str, Any]] = []
    source: Literal["fixture", "disk", "executed", "executed_partial"] = "disk"
    fixture = load_reliability_full_fixture()
    run_ids: list[str] = []
    if fixture and fixture.get("golden_revision") == revision:
        run_ids = list(fixture.get("run_ids") or [])[:n]
        loaded = [_load_manifest(rid) for rid in run_ids]
        if len(loaded) == n and all(m and _is_full_resilient_manifest(m, expected_revision=revision) for m in loaded):
            manifests = loaded  # type: ignore[list-item]
            source = "fixture"

    if not manifests:
        run_ids = list_full_resilient_run_ids(revision=revision, limit=n)
        loaded = [_load_manifest(rid) for rid in run_ids]
        loaded_ok = [m for m in loaded if m and _is_full_resilient_manifest(m, expected_revision=revision)]
        if len(loaded_ok) >= n:
            manifests = loaded_ok[:n]
            source = "disk"
            if not fixture:
                save_reliability_full_fixture(
                    [str(m.get("run_id")) for m in manifests],
                    revision=revision,
                )

    if len(manifests) < n:
        missing = n - len(manifests)
        source = "executed_partial" if manifests else "executed"
        for _ in range(missing):
            manifests.append(run_eval(arch, persist=True, cases=all_cases, fast_mode=False))
        if len(manifests) >= n:
            save_reliability_full_fixture(
                [str(m.get("run_id")) for m in manifests[:n]],
                revision=revision,
            )
            source = "executed" if missing == n else "executed_partial"

    resumo = summarize_reliability(manifests[:n])
    manifests = manifests[:n]
    return {
        "manifests": manifests,
        "resumo": resumo,
        "rates_df": reliability_rates_frame(manifests),
        "variation_df": reliability_variation_frame(manifests),
        "source": source,
        "fast_mode": False,
        "fixture_path": str(_RELIABILITY_FULL_FIXTURE),
    }


def reliability_from_run_ids(run_ids: list[str]) -> dict[str, Any]:
    """Load persisted manifests by ``run_id`` and summarize reliability.

    Args:
        run_ids: One manifest per repetition (same arch and golden-set).

    Returns:
        ``{"manifests": [...], "resumo": summarize_reliability(...)}``.
    """
    manifests: list[dict[str, Any]] = []
    for run_id in run_ids:
        manifest = _load_manifest(run_id)
        if manifest is None:
            raise FileNotFoundError(f"Manifest não encontrado: {run_id}")
        manifests.append(manifest)
    resumo = summarize_reliability(manifests)
    return {
        "manifests": manifests,
        "resumo": resumo,
        "rates_df": reliability_rates_frame(manifests),
        "variation_df": reliability_variation_frame(manifests),
    }
