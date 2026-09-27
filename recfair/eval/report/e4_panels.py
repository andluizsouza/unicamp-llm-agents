"""Tables for the E4 notebook (consolidation, Wilson, ethics)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from eval.cases import is_frozen_ruler_case
from eval.ethics import CONSEQUENCE_MATRIX, breakdown_by, metrica_ponderada, simple_accuracy
from eval.glossary import ARCHITECTURE_LABELS
from eval.stats import intervalo_wilson, sobrepoe


def frozen_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """T01–T60 subset."""
    return [row for row in records if is_frozen_ruler_case(row.get("case") or {})]


def _median_latency(records: list[dict[str, Any]]) -> float | None:
    values = sorted(float((row.get("metrics") or {}).get("latencia_s") or 0.0) for row in records)
    if not values:
        return None
    mid = len(values) // 2
    if len(values) % 2:
        return round(values[mid], 2)
    return round((values[mid - 1] + values[mid]) / 2.0, 2)


def consolidate_versions(
    manifests: dict[str, dict[str, Any]],
    *,
    reliability: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """One row per architecture: counts, rate, cost, latency, characteristic failures."""
    rows: list[dict[str, Any]] = []
    for arch, manifest in manifests.items():
        records = frozen_records(list(manifest.get("records") or []))
        acc = simple_accuracy(records, frozen_only=False)
        weighted = metrica_ponderada(records, frozen_only=False)
        llm = sum(int((row.get("metrics") or {}).get("chamadas_llm") or 0) for row in records)
        tools = sum(int((row.get("metrics") or {}).get("tool_calls") or 0) for row in records)
        cost = (manifest.get("resumo") or {}).get("custo_estimado_usd")
        faixa = None
        if reliability and reliability.get("architecture_id") == arch:
            faixa = reliability.get("faixa")
        elif arch == "resilient" and reliability:
            faixa = reliability.get("faixa")
        acertos = acc["acertos"] or 0
        total = acc["total"] or 0
        lo, hi = intervalo_wilson(acertos, total)
        rows.append(
            {
                "versao": ARCHITECTURE_LABELS.get(arch, arch),
                "arch": arch,
                "acertos": f"{acertos} de {total}",
                "taxa": acc["taxa"],
                "wilson_lo": round(lo, 4),
                "wilson_hi": round(hi, 4),
                "ponderada": weighted.get("score"),
                "faixa": faixa,
                "chamadas_llm": llm,
                "tool_calls": tools,
                "latencia_mediana_s": _median_latency(records),
                "custo_usd": cost,
            }
        )
    return pd.DataFrame(rows)


def wilson_overlap_table(df: pd.DataFrame) -> pd.DataFrame:
    """Pairwise Wilson-interval overlap for architecture rates."""
    rows: list[dict[str, Any]] = []
    items = list(df.to_dict(orient="records"))
    for i, left in enumerate(items):
        for right in items[i + 1 :]:
            a = (float(left["wilson_lo"]), float(left["wilson_hi"]))
            b = (float(right["wilson_lo"]), float(right["wilson_hi"]))
            rows.append(
                {
                    "par": f"{left['arch']} × {right['arch']}",
                    "sobrepoe": sobrepoe(a, b),
                    "intervalo_a": a,
                    "intervalo_b": b,
                }
            )
    return pd.DataFrame(rows)


def case_changes_table(manifests: dict[str, dict[str, Any]]) -> pd.DataFrame:
    """Per-case pass/fail across architectures (frozen ruler)."""
    by_id: dict[str, dict[str, Any]] = {}
    for arch, manifest in manifests.items():
        for row in frozen_records(list(manifest.get("records") or [])):
            case_id = str((row.get("case") or {}).get("id") or "")
            by_id.setdefault(case_id, {"caso": case_id})
            by_id[case_id][arch] = bool((row.get("check") or {}).get("aprovado"))
    return pd.DataFrame(list(by_id.values())).sort_values("caso")


def weighted_vs_simple_table(manifests: dict[str, dict[str, Any]]) -> pd.DataFrame:
    """Simple accuracy vs harm-weighted score; used to compare rankings."""
    rows: list[dict[str, Any]] = []
    for arch, manifest in manifests.items():
        records = frozen_records(list(manifest.get("records") or []))
        simple = simple_accuracy(records, frozen_only=False)
        weighted = metrica_ponderada(records, frozen_only=False)
        rows.append(
            {
                "arch": arch,
                "versao": ARCHITECTURE_LABELS.get(arch, arch),
                "taxa_simples": simple["taxa"],
                "acertos": simple["acertos"],
                "total": simple["total"],
                "score_ponderado": weighted["score"],
                "mean_harm": weighted["mean_harm"],
            }
        )
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["rank_simples"] = frame["taxa_simples"].rank(ascending=False, method="min")
        frame["rank_ponderado"] = frame["score_ponderado"].rank(ascending=False, method="min")
    return frame


def type_breakdown_table(records: list[dict[str, Any]], field: str = "tipo") -> pd.DataFrame:
    """Error distribution by case type."""
    return pd.DataFrame(breakdown_by(frozen_records(records), field=field))


def consequence_matrix_table() -> pd.DataFrame:
    """Static consequence matrix aligned with GRAVIDADE weights."""
    return pd.DataFrame(CONSEQUENCE_MATRIX)


def unusual_profile_rows(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Cases beyond T01–T60 (empty while the golden-set stays at 60)."""
    rows: list[dict[str, Any]] = []
    for row in records:
        case = row.get("case") or {}
        if is_frozen_ruler_case(case):
            continue
        check = row.get("check") or {}
        rows.append(
            {
                "caso": case.get("id"),
                "tipo": case.get("tipo"),
                "familia": case.get("familia"),
                "entrada": case.get("entrada"),
                "aprovado": check.get("aprovado"),
                "severity": check.get("severity"),
                "ndcg_at_5": check.get("ndcg_at_5"),
                "target_hit": check.get("g_target_hit"),
            }
        )
    return pd.DataFrame(rows)
