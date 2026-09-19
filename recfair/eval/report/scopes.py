"""E3 scope aggregation and context summaries."""

from __future__ import annotations

from typing import Any

import pandas as pd

from eval.contexts import EVAL_CONTEXTS, filter_records_by_context, routing_destination
from eval.metrics import FAQ_SEMANTIC_THRESHOLD
from eval.report.html import render_comparison_report
from eval.report.legacy import summarize_records


def _case_number(case_id: str) -> int:
    digits = "".join(ch for ch in case_id if ch.isdigit())
    return int(digits) if digits else 0


def e3_scope_of(case: dict[str, Any]) -> str | None:
    """Map T01–T38 to an E3 evaluation scope; T39+ return None."""
    number = _case_number(case.get("id", ""))
    if 1 <= number <= 15:
        return "restrict_core"
    if 16 <= number <= 30:
        return "gap"
    if 31 <= number <= 33:
        return "memory"
    if 34 <= number <= 38:
        return "scoring"
    return None


def _recommendation_block(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate ranking metrics for the recomendacao context."""
    block = _scope_block(records)
    block["case_ids"] = [record["case"]["id"] for record in records]
    return block


def _security_block(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate guardrail pass rate for the seguranca context."""
    n = len(records)
    if not n:
        return {"n": 0, "pass_rate": None, "guardrail_hit_rate": None, "case_ids": []}
    passed = sum(1 for record in records if record["check"]["aprovado"])
    guardrail_hits = sum(
        1
        for record in records
        if record["check"].get("pii_hits")
        or record["check"].get("injection_hits")
        or record["check"].get("jailbreak_hits")
    )
    return {
        "n": n,
        "pass_rate": round(passed / n, 4),
        "guardrail_hit_rate": round(guardrail_hits / n, 4),
        "case_ids": [record["case"]["id"] for record in records],
    }


def _faq_block(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate semantic similarity for the faq context (E3 only)."""
    n = len(records)
    scores = [
        float(record["check"]["faq_semantic_similarity"])
        for record in records
        if record["check"].get("faq_semantic_similarity") is not None
    ]
    passed = sum(1 for record in records if record["check"]["aprovado"])
    return {
        "n": n,
        "mean_semantic_similarity": round(sum(scores) / len(scores), 4) if scores else None,
        "semantic_threshold": FAQ_SEMANTIC_THRESHOLD,
        "pass_rate": round(passed / n, 4) if n else None,
        "case_ids": [record["case"]["id"] for record in records],
    }


def _rate_passed(records: list[dict[str, Any]]) -> float | None:
    if not records:
        return None
    passed = sum(1 for record in records if record["check"]["aprovado"])
    return round(passed / len(records), 4)


def _routing_block(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate supervisor routing accuracy (E3 only)."""
    by_dest: dict[str, list[dict[str, Any]]] = {
        "recomendação": [],
        "perguntas frequentes": [],
        "transbordo": [],
        "fora de contexto": [],
    }
    for record in records:
        dest = routing_destination(record["case"])
        by_dest.setdefault(dest, []).append(record)
    return {
        "n": len(records),
        "routing_pass_rate": _rate_passed(records),
        "case_ids": [record["case"]["id"] for record in records],
        "by_destination": {
            dest: {
                "n": len(subset),
                "pass_rate": _rate_passed(subset),
                "case_ids": [record["case"]["id"] for record in subset],
            }
            for dest, subset in by_dest.items()
            if subset
        },
    }


def summarize_by_context(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Aggregate metrics per evaluation context."""
    blocks: dict[str, dict[str, Any]] = {}
    for context in EVAL_CONTEXTS:
        subset = filter_records_by_context(records, context)
        if context == "recomendacao":
            blocks[context] = _recommendation_block(subset)
        elif context == "seguranca":
            blocks[context] = _security_block(subset)
        elif context == "faq":
            blocks[context] = _faq_block(subset)
        else:
            blocks[context] = _routing_block(subset)
    return blocks


def _scope_block(records: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(records)
    ndcgs = [
        float(r["check"]["ndcg_at_5"])
        for r in records
        if r.get("check", {}).get("ndcg_at_5") is not None
    ]
    exact_flags = [bool(r.get("check", {}).get("aprovado_exact")) for r in records]
    dist = {"none": 0, "minor": 0, "moderate": 0, "grave": 0}
    for record in records:
        severity = record.get("check", {}).get("severity") or "grave"
        if severity in dist:
            dist[severity] += 1
    return {
        "mean_ndcg_at_5": round(sum(ndcgs) / len(ndcgs), 4) if ndcgs else None,
        "aprovado_exact_rate": round(sum(exact_flags) / n, 4) if n else None,
        "severity_distribution": dist,
        "grave_error_rate": round(dist["grave"] / n, 4) if n else None,
        "n": n,
    }


def summarize_records_v3(records: list[dict[str, Any]]) -> dict[str, Any]:
    """E3 ruler aggregates plus the legacy ``e1_`` / ``e2_`` keys."""
    from eval.requirements import summarize_by_requirement

    legacy = summarize_records(records)
    by_scope: dict[str, list[dict[str, Any]]] = {
        "restrict_core": [],
        "gap": [],
        "memory": [],
        "scoring": [],
        "overall": [],
    }
    for record in records:
        scope = e3_scope_of(record["case"])
        if scope:
            by_scope[scope].append(record)
            by_scope["overall"].append(record)

    e3_restrict = _scope_block(by_scope["restrict_core"])
    e3_gap = _scope_block(by_scope["gap"])
    gap_flags = [
        r["check"].get("gap_intentional_pass")
        for r in by_scope["gap"]
        if r["check"].get("gap_intentional_pass") is not None
    ]
    e3_gap["gap_intentional_pass_rate"] = (
        round(sum(1 for flag in gap_flags if flag) / len(gap_flags), 4) if gap_flags else None
    )
    e3_gap["false_positive_gap_count"] = sum(
        1 for r in by_scope["gap"] if r["check"].get("false_positive_gap")
    )

    rf_df = summarize_by_requirement(records)
    by_context = summarize_by_context(records)
    return {
        **legacy,
        "e3_restrict_core": e3_restrict,
        "e3_gap": e3_gap,
        "e3_memory": _scope_block(by_scope["memory"]),
        "e3_scoring": _scope_block(by_scope["scoring"]),
        "e3_overall": _scope_block(by_scope["overall"]),
        "e3_by_context": by_context,
        "rf_breakdown": rf_df.to_dict(orient="records"),
    }
def render_rf_breakdown_table(
    resumo_v3: dict[str, Any],
    *,
    title: str = "Requisitos funcionais (referência)",
) -> str:
    """HTML table of RF pass rates from ``summarize_records_v3``."""
    rows = resumo_v3.get("rf_breakdown") or []
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(
            [{"requisito": "—", "conceito": "—", "passou": 0, "total": 0, "taxa": None}]
        )
    column_order = ["requisito", "conceito", "passou", "total", "taxa"]
    df = df[[col for col in column_order if col in df.columns]]
    return render_comparison_report(
        df,
        status_col="requisito",
        title=title,
        subtitle=(
            "Cada RF resume um contrato do RecFair E1. "
            "Vazio no denominador = requisito não aplicável ao caso."
        ),
        code_columns=frozenset({"requisito", "conceito"}),
        show_legend=False,
    )


def render_scope_metrics_panel(
    resumo_v3: dict[str, Any],
    *,
    title: str = "Régua E3 por escopo",
) -> str:
    """HTML panel of nDCG / exact / severity per E3 scope."""
    keys = [
        ("e3_restrict_core", "restrict_core (T01–T15)"),
        ("e3_gap", "gap (T16–T30)"),
        ("e3_memory", "memory (T31–T33)"),
        ("e3_scoring", "scoring (T34–T38)"),
        ("e3_overall", "overall (T01–T38)"),
    ]
    rows = []
    for key, label in keys:
        block = resumo_v3.get(key) or {}
        dist = block.get("severity_distribution") or {}
        row = {
            "escopo": label,
            "n": block.get("n"),
            "mean_ndcg@5": block.get("mean_ndcg_at_5"),
            "aprovado_exact": block.get("aprovado_exact_rate"),
            "grave_error_rate": block.get("grave_error_rate"),
            "none/minor/mod/grave": (
                f"{dist.get('none', 0)}/{dist.get('minor', 0)}/"
                f"{dist.get('moderate', 0)}/{dist.get('grave', 0)}"
            ),
        }
        if key == "e3_gap":
            row["gap_intentional_pass"] = block.get("gap_intentional_pass_rate")
            row["false_positive_gap"] = block.get("false_positive_gap_count")
        rows.append(row)
    df = pd.DataFrame(rows)
    return render_comparison_report(
        df,
        status_col="escopo",
        title=title,
        subtitle="nDCG@5 só em casos com lista; abstenção correta não entra na média.",
    )


def filter_records_by_ids(
    records: list[dict[str, Any]],
    *,
    max_number: int | None = None,
    min_number: int = 1,
) -> list[dict[str, Any]]:
    """Subset runner records by golden-case id number (inclusive)."""
    selected = []
    for record in records:
        number = _case_number(record["case"]["id"])
        if number < min_number:
            continue
        if max_number is not None and number > max_number:
            continue
        selected.append(record)
    return selected
