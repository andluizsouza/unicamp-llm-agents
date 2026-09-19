"""Notebook report tables and HTML panels."""

from __future__ import annotations

from typing import Any

import pandas as pd

from eval.contexts import (
    CONTEXT_ARCHITECTURES,
    CONTEXT_LABELS,
    EVAL_CONTEXTS,
    EvalContext,
    eval_context_of,
    filter_records_by_context,
    routing_destination,
)
from eval.glossary import ARCHITECTURE_LABELS, CONTEXT_SECTIONS
from eval.metrics import FAQ_SEMANTIC_THRESHOLD
from eval.verify import (
    diagnose_failure,
    escopo_label,
    final_status,
    format_baseline_col,
    format_gabarito_col,
    gold_diff_label,
    is_restrict_scope,
    motivo_sucesso,
)


def build_results_table(
    records: list[dict[str, Any]],
    *,
    output_column: str = "baseline",
    experiment: str = "e1",
) -> pd.DataFrame:
    """Build per-case comparison table from runner records."""
    rows = []
    for rec in records:
        case = rec["case"]
        check = rec["check"]
        restrict = is_restrict_scope(case["familia"])
        motivo = motivo_sucesso(case, check, experiment=experiment) or diagnose_failure(
            case, check, experiment=experiment
        )
        status = final_status(check["aprovado"], restrict)
        rows.append(
            {
                "caso": case["id"],
                "tipo_caso": case["tipo"],
                "tipo_teste": escopo_label(restrict),
                "status_final": status,
                output_column: format_baseline_col(check),
                "gabarito": format_gabarito_col(case, check),
                "diff": gold_diff_label(check["skus"], check["gold"]),
                "motivo_erro": motivo or "—",
            }
        )
    return pd.DataFrame(rows)


_STATUS_ACCENT = {
    "sucesso": "#198754",
    "erro": "#dc3545",
    "erro*": "#fd7e14",
}

_STATUS_BADGE = {
    "sucesso": ("#d1e7dd", "#0a3622", "#a3cfbb"),
    "erro": ("#f8d7da", "#58151c", "#f1aeb5"),
    "erro*": ("#fff3cd", "#664d03", "#ffe69c"),
}

_STATUS_COLUMNS = frozenset({"status_final", "resultado"})


def _normalize_status(raw: str) -> str:
    """Map row status labels to the canonical sucesso / erro / erro* palette."""
    text = str(raw).strip()
    if text in _STATUS_ACCENT:
        return text
    aliases = {"aprovado": "sucesso", "reprovado": "erro"}
    return aliases.get(text, "")


def _status_badge(status: str) -> str:
    canonical = _normalize_status(status) or status
    bg, fg, border = _STATUS_BADGE.get(canonical, ("#e9ecef", "#343a40", "#ced4da"))
    return (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:999px;'
        f"background:{bg};color:{fg};border:1px solid {border};"
        f'font-weight:600;font-size:12px;letter-spacing:0.02em;">{status}</span>'
    )


def _fmt_cell(
    col: str,
    text: str,
    status: str,
    *,
    code_columns: frozenset[str] | None = None,
) -> str:
    base = "padding:10px 12px;border-bottom:1px solid #e9ecef;color:#212529;vertical-align:top;"
    code_cols = code_columns or frozenset({"baseline", "gabarito"})
    if col in _STATUS_COLUMNS:
        canonical = _normalize_status(text)
        if canonical:
            return f'<td style="{base}">{_status_badge(canonical)}</td>'
    if col in code_cols:
        return (
            f'<td style="{base}">'
            f'<code style="font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;'
            f"font-size:12px;color:#212529;background:#f8f9fa;padding:4px 6px;"
            f'border-radius:4px;display:inline-block;max-width:420px;word-break:break-all;">'
            f"{text}</code></td>"
        )
    if col == "motivo_erro" and text not in {"—", ""}:
        return f'<td style="{base}background:#fff5f5;color:#842029;font-size:12px;">{text}</td>'
    if col == "diff" and text not in {"—", "", "igual ao gabarito"}:
        return f'<td style="{base}background:#fff8e6;color:#664d03;font-size:12px;">{text}</td>'
    return f'<td style="{base}">{text}</td>'


def _render_table_body(
    df: pd.DataFrame,
    status_col: str = "status_final",
    *,
    code_columns: frozenset[str] | None = None,
    show_legend: bool = True,
) -> str:
    parts = [
        '<table style="border-collapse:collapse;width:100%;min-width:720px;background:#ffffff;">',
        "<thead><tr>",
    ]
    for col in df.columns:
        label = str(col).replace("_", " ")
        parts.append(
            f'<th style="padding:10px 12px;background:#374151;color:#f9fafb;text-align:left;'
            f'font-size:11px;text-transform:uppercase;letter-spacing:0.06em;border-bottom:1px solid #4b5563;">'
            f"{label}</th>"
        )
    parts.append("</tr></thead><tbody>")
    for i, row in df.iterrows():
        st = _normalize_status(str(row.get(status_col, "")))
        stripe = "#f9fafb" if i % 2 else "#ffffff"
        border_color = _STATUS_ACCENT.get(st, "#9ca3af")
        parts.append(f'<tr style="background:{stripe};">')
        for j, col in enumerate(df.columns):
            val = row[col]
            if val is None or (isinstance(val, float) and pd.isna(val)):
                text = "—"
            else:
                text = str(val)
            if j == 0:
                parts.append(
                    f'<td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;border-left:4px solid {border_color};'
                    f'color:#111827;font-weight:700;font-variant-numeric:tabular-nums;vertical-align:top;">{text}</td>'
                )
            else:
                parts.append(_fmt_cell(col, text, st, code_columns=code_columns))
        parts.append("</tr>")
    parts.append("</tbody></table>")
    if show_legend:
        parts.append(
            '<div style="display:flex;flex-wrap:wrap;gap:14px;padding:10px 14px 12px;font-size:12px;'
            'color:#374151;background:#f9fafb;border-top:1px solid #e5e7eb;">'
            '<span style="color:#111827;"><span style="display:inline-block;width:10px;height:10px;border-radius:2px;'
            f'background:{_STATUS_ACCENT["sucesso"]};margin-right:6px;"></span>'
            "sucesso (restrito ou gap acertado)</span>"
            '<span style="color:#111827;"><span style="display:inline-block;width:10px;height:10px;border-radius:2px;'
            f'background:{_STATUS_ACCENT["erro"]};margin-right:6px;"></span>'
            "erro (restrito)</span>"
            '<span style="color:#111827;"><span style="display:inline-block;width:10px;height:10px;border-radius:2px;'
            f'background:{_STATUS_ACCENT["erro*"]};margin-right:6px;"></span>'
            "erro* (gap falhou)</span>"
            "</div>"
        )
    return "".join(parts)


_PANEL = (
    "color-scheme:only light;forced-color-adjust:none;"
    "background:#ffffff;color:#111827;"
    "border:1px solid #9ca3af;border-radius:12px;"
    "overflow:hidden;margin:0.75rem 0;"
    "box-shadow:0 2px 10px rgba(0,0,0,.18);"
    "font-family:system-ui,-apple-system,Segoe UI,sans-serif;"
)
_PANEL_HDR = "background:#1e293b;color:#f8fafc;padding:14px 18px;border-bottom:2px solid #334155;"


def render_comparison_report(
    df: pd.DataFrame,
    status_col: str = "status_final",
    *,
    title: str = "Baseline × gabarito (golden-set)",
    subtitle: str = "Comparação determinística: mesmos SKUs e mesma ordem = sucesso.",
    code_columns: frozenset[str] | None = None,
    show_legend: bool | None = None,
) -> str:
    if show_legend is None:
        show_legend = status_col in _STATUS_COLUMNS
    return (
        f'<div style="{_PANEL}">'
        f'<div style="{_PANEL_HDR}">'
        f'<div style="font-size:1.08rem;font-weight:700;color:#ffffff;margin:0;'
        f'letter-spacing:-0.01em;">{title}</div>'
        f'<div style="font-size:12px;color:#e2e8f0;margin-top:5px;line-height:1.4;">'
        f"{subtitle}</div>"
        "</div>"
        f'<div style="overflow-x:auto;background:#ffffff;">'
        f"{_render_table_body(df, status_col, code_columns=code_columns, show_legend=show_legend)}</div>"
        "</div>"
    )


def render_metrics_panel(
    resumo: dict[str, Any],
    restrict_ok: int | None = None,
    restrict_n: int | None = None,
    overall_ok: int | None = None,
    overall_n: int | None = None,
    *,
    title: str = "Métricas consolidadas",
    metric_prefix: str = "e1",
    subtitle: str = "Run do baseline V1",
    rate_restrict_label: str | None = None,
    rate_restrict_hint: str = "T01–T15 · baseline deve acertar",
    rate_overall_label: str | None = None,
    rate_overall_hint: str = "T01–T30 · T16–T30 = gaps G",
) -> str:
    """Render consolidated metrics HTML panel from a runner ``resumo`` dict.

    Count arguments default to ``{metric_prefix}_rate_*_{n,d}`` keys in ``resumo``.
    Explicit counts remain supported for E1 notebooks that compute them separately.
    """
    restrict_ok = (
        restrict_ok if restrict_ok is not None else resumo[f"{metric_prefix}_rate_restrict_n"]
    )
    restrict_n = (
        restrict_n if restrict_n is not None else resumo[f"{metric_prefix}_rate_restrict_d"]
    )
    overall_ok = overall_ok if overall_ok is not None else resumo[f"{metric_prefix}_rate_overall_n"]
    overall_n = overall_n if overall_n is not None else resumo[f"{metric_prefix}_rate_overall_d"]
    restrict_label = rate_restrict_label or f"{metric_prefix}_rate_restrict"
    overall_label = rate_overall_label or f"{metric_prefix}_rate_overall"
    rb = lambda ok, n: f"{ok}/{n} ({100 * ok / n:.1f}%)" if n else "—"
    return (
        f'<div style="{_PANEL}max-width:640px;">'
        f'<div style="{_PANEL_HDR}">'
        f'<div style="font-size:1.08rem;font-weight:700;color:#ffffff;margin:0;">'
        f"{title}</div>"
        f'<div style="font-size:12px;color:#e2e8f0;margin-top:5px;">'
        f"{subtitle}</div>"
        "</div>"
        '<table style="border-collapse:collapse;width:100%;background:#ffffff;color:#111827;">'
        f'<tr><td style="padding:11px 16px;border-bottom:1px solid #e5e7eb;background:#f9fafb;color:#111827;">'
        f"<b>{restrict_label}</b><br>"
        f'<small style="color:#4b5563;">{rate_restrict_hint}</small></td>'
        f'<td style="padding:11px 16px;border-bottom:1px solid #e5e7eb;font-size:1.15em;color:#111827;">'
        f"<b>{rb(restrict_ok, restrict_n)}</b></td></tr>"
        f'<tr><td style="padding:11px 16px;border-bottom:1px solid #e5e7eb;background:#f9fafb;color:#111827;">'
        f"<b>{overall_label}</b><br>"
        f'<small style="color:#4b5563;">{rate_overall_hint}</small></td>'
        f'<td style="padding:11px 16px;border-bottom:1px solid #e5e7eb;font-size:1.15em;color:#111827;">'
        f"<b>{rb(overall_ok, overall_n)}</b></td></tr>"
        f'<tr><td style="padding:10px 16px;border-bottom:1px solid #e5e7eb;color:#4b5563;">Latência mediana</td>'
        f'<td style="padding:10px 16px;border-bottom:1px solid #e5e7eb;color:#111827;">'
        f"<b>{resumo['latencia_mediana_s']} s</b></td></tr>"
        f'<tr><td style="padding:10px 16px;border-bottom:1px solid #e5e7eb;color:#4b5563;">Latência média</td>'
        f'<td style="padding:10px 16px;border-bottom:1px solid #e5e7eb;color:#111827;">'
        f"<b>{resumo['latencia_media_s']} s</b></td></tr>"
        f'<tr><td style="padding:10px 16px;border-bottom:1px solid #e5e7eb;color:#4b5563;">Chamadas LLM</td>'
        f'<td style="padding:10px 16px;border-bottom:1px solid #e5e7eb;color:#111827;">'
        f"<b>{resumo['chamadas_llm']}</b></td></tr>"
        f'<tr><td style="padding:10px 16px;border-bottom:1px solid #e5e7eb;color:#4b5563;">Tokens entrada / saída</td>'
        f'<td style="padding:10px 16px;border-bottom:1px solid #e5e7eb;color:#111827;">'
        f"<b>{resumo['tokens_entrada']:,}</b> / <b>{resumo['tokens_saida']:,}</b></td></tr>"
        f'<tr><td style="padding:10px 16px;color:#4b5563;">Custo estimado (USD)</td>'
        f'<td style="padding:10px 16px;color:#111827;">'
        f"<b>${resumo['custo_estimado_usd']:.4f}</b></td></tr>"
        "</table></div>"
    )


def _familia_bucket(familia: str) -> str:
    if familia == "S_memory":
        return "memory"
    if familia.startswith("S_scoring_"):
        return "scoring"
    if familia.startswith("S_"):
        return "restrict_core"
    return "global"


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate eval metrics from runner records."""
    df = pd.DataFrame(
        [
            {
                "aprovado": r["check"]["aprovado"],
                "restrict": is_restrict_scope(r["case"]["familia"]),
                "bucket": _familia_bucket(r["case"]["familia"]),
                "latencia_s": r["metrics"]["latencia_s"],
                "tokens_entrada": r["metrics"].get("tokens_entrada"),
                "tokens_saida": r["metrics"].get("tokens_saida"),
                "chamadas_llm": r["metrics"]["chamadas_llm"],
                "tool_calls": r["metrics"].get("tool_calls", 0),
            }
            for r in records
        ]
    )
    restrict_df = df[df["restrict"]]
    n_restrict_ok = int(restrict_df["aprovado"].sum())
    n_restrict = len(restrict_df)
    n_overall_ok = int(df["aprovado"].sum())
    n_overall = len(df)
    tok_in_series = pd.to_numeric(df["tokens_entrada"], errors="coerce")
    tok_out_series = pd.to_numeric(df["tokens_saida"], errors="coerce")
    tok_in = tok_in_series.fillna(0).sum()
    tok_out = tok_out_series.fillna(0).sum()
    lat = pd.to_numeric(df["latencia_s"], errors="coerce")
    from recfair.config import USD_PER_1M_INPUT_TOKENS, USD_PER_1M_OUTPUT_TOKENS
    from recfair.observability.cost import estimate_llm_cost_usd

    scoring_df = df[df["bucket"] == "scoring"]
    memory_df = df[df["bucket"] == "memory"]
    n_scoring_ok = int(scoring_df["aprovado"].sum()) if len(scoring_df) else 0
    n_scoring = len(scoring_df)
    n_memory_ok = int(memory_df["aprovado"].sum()) if len(memory_df) else 0
    n_memory = len(memory_df)
    tool_calls = int(df["tool_calls"].sum()) if len(df) else 0

    rate_restrict = round(n_restrict_ok / n_restrict, 4) if n_restrict else None
    rate_overall = round(n_overall_ok / n_overall, 4) if n_overall else None

    return {
        "e1_rate_restrict": rate_restrict,
        "e2_rate_restrict": rate_restrict,
        "e1_rate_restrict_n": n_restrict_ok,
        "e1_rate_restrict_d": n_restrict,
        "e2_rate_restrict_n": n_restrict_ok,
        "e2_rate_restrict_d": n_restrict,
        "e2_rate_scoring": round(n_scoring_ok / n_scoring, 4) if n_scoring else None,
        "e2_rate_scoring_n": n_scoring_ok,
        "e2_rate_scoring_d": n_scoring,
        "e2_rate_memory": round(n_memory_ok / n_memory, 4) if n_memory else None,
        "e2_rate_memory_n": n_memory_ok,
        "e2_rate_memory_d": n_memory,
        "e1_rate_overall": rate_overall,
        "e2_rate_overall": rate_overall,
        "e1_rate_overall_n": n_overall_ok,
        "e1_rate_overall_d": n_overall,
        "e2_rate_overall_n": n_overall_ok,
        "e2_rate_overall_d": n_overall,
        "latencia_mediana_s": round(float(lat.median()), 2) if len(lat) else None,
        "latencia_media_s": round(float(lat.mean()), 2) if len(lat) else None,
        "chamadas_llm": int(df["chamadas_llm"].sum()) if len(df) else 0,
        "tool_calls": tool_calls,
        "tokens_entrada": int(tok_in),
        "tokens_saida": int(tok_out),
        "tokens_entrada_media": round(float(tok_in_series.mean()), 1)
        if len(tok_in_series)
        else None,
        "tokens_saida_media": round(float(tok_out_series.mean()), 1)
        if len(tok_out_series)
        else None,
        "custo_estimado_usd": round(estimate_llm_cost_usd(tok_in, tok_out), 6),
        "nota_custo": (
            f"${USD_PER_1M_INPUT_TOKENS}/1M in, ${USD_PER_1M_OUTPUT_TOKENS}/1M out (thinking incl.)"
        ),
    }


def _manifest_resumo(manifest: dict[str, Any]) -> dict[str, Any]:
    """Return resumo, recomputing from records when needed for older runs."""
    resumo = manifest.get("resumo", {})
    records = manifest.get("records")
    if records and ("tokens_entrada_media" not in resumo or "tokens_saida_media" not in resumo):
        resumo = {**resumo, **summarize_records(records)}
    return resumo


def build_arch_comparison_table(
    manifest_baseline: dict[str, Any],
    manifest_workflow: dict[str, Any],
    *,
    left_label: str | None = None,
    right_label: str | None = None,
    metric_prefix: str = "e2",
) -> pd.DataFrame:
    """Side-by-side architecture metrics from two run manifests."""
    left = left_label or manifest_baseline.get("architecture_id", "baseline")
    right = right_label or manifest_workflow.get("architecture_id", "workflow")
    rows = []
    metrics = [
        (f"{metric_prefix}_rate_restrict", "Restrito (S_*)"),
        (f"{metric_prefix}_rate_scoring", "Scoring (T34–T38)"),
        (f"{metric_prefix}_rate_memory", "Memória (T31–T33)"),
        (f"{metric_prefix}_rate_overall", "Geral"),
        ("latencia_mediana_s", "Latência mediana (s)"),
        ("tokens_entrada_media", "Tokens entrada média"),
        ("tokens_saida_media", "Tokens saída média"),
        ("chamadas_llm", "Chamadas LLM"),
        ("tool_calls", "Chamadas tools"),
        ("custo_estimado_usd", "Custo est. (USD)"),
    ]
    b_resumo = _manifest_resumo(manifest_baseline)
    w_resumo = _manifest_resumo(manifest_workflow)
    for key, label in metrics:
        b_val = b_resumo.get(key)
        w_val = w_resumo.get(key)
        delta = None
        if isinstance(b_val, (int, float)) and isinstance(w_val, (int, float)):
            if (
                key.endswith("_rate_restrict")
                or key.endswith("_rate_scoring")
                or key.endswith("_rate_memory")
                or key.endswith("_rate_overall")
            ):
                delta = round(w_val - b_val, 4)
            elif key.startswith("tokens_"):
                delta = round(w_val - b_val, 1)
            else:
                delta = round(w_val - b_val, 2)
        rows.append(
            {
                "métrica": label,
                left: b_val,
                right: w_val,
                "delta": delta,
            }
        )
    return pd.DataFrame(rows)


def render_arch_comparison(
    manifest_baseline: dict[str, Any],
    manifest_workflow: dict[str, Any],
    *,
    title: str | None = None,
    subtitle: str | None = None,
    left_label: str | None = None,
    right_label: str | None = None,
    metric_prefix: str = "e2",
) -> str:
    """HTML panel comparing two architecture run manifests."""
    left = left_label or manifest_baseline.get("architecture_id", "baseline")
    right = right_label or manifest_workflow.get("architecture_id", "workflow")
    df = build_arch_comparison_table(
        manifest_baseline,
        manifest_workflow,
        left_label=left,
        right_label=right,
        metric_prefix=metric_prefix,
    )
    revision = manifest_baseline.get("golden_revision", "—")
    panel_title = title or f"Comparação {left} × {right}"
    panel_subtitle = subtitle or (f"golden_revision={revision} · mesmo modelo · mesma sessão")
    return (
        f'<div style="{_PANEL}">'
        f'<div style="{_PANEL_HDR}">'
        f'<div style="font-size:1.08rem;font-weight:700;color:#ffffff;">'
        f"{panel_title}</div>"
        f'<div style="font-size:12px;color:#cbd5e1;margin-top:4px;">'
        f"{panel_subtitle}</div></div>"
        f'<div style="padding:0;overflow-x:auto;">{_render_table_body(df, "métrica")}</div>'
        "</div>"
    )


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


def build_agent_cost_table(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Aggregate latency / LLM / tools / tokens / cost by ``agent_id``."""
    from recfair.observability.cost import estimate_llm_cost_usd

    rows: dict[str, dict[str, float]] = {}
    for record in records:
        for step in record.get("metrics", {}).get("agent_traces") or []:
            agent_id = step.get("agent_id") or "?"
            bucket = rows.setdefault(
                agent_id,
                {
                    "latencia_s": 0.0,
                    "chamadas_llm": 0.0,
                    "tool_calls": 0.0,
                    "tokens_entrada": 0.0,
                    "tokens_saida": 0.0,
                    "custo_usd": 0.0,
                    "n": 0.0,
                },
            )
            bucket["latencia_s"] += float(step.get("latencia_s") or 0)
            bucket["chamadas_llm"] += float(step.get("chamadas_llm") or 0)
            bucket["tool_calls"] += float(step.get("tool_calls") or 0)
            bucket["tokens_entrada"] += float(step.get("tokens_entrada") or 0)
            bucket["tokens_saida"] += float(step.get("tokens_saida") or 0)
            if step.get("custo_usd") is not None:
                bucket["custo_usd"] += float(step["custo_usd"])
            else:
                bucket["custo_usd"] += estimate_llm_cost_usd(
                    step.get("tokens_entrada") or 0,
                    step.get("tokens_saida") or 0,
                )
            bucket["n"] += 1
    data = []
    for agent_id, bucket in sorted(rows.items()):
        data.append(
            {
                "agente": agent_id,
                "passos": int(bucket["n"]),
                "latencia_s": round(bucket["latencia_s"], 2),
                "chamadas_llm": int(bucket["chamadas_llm"]),
                "tool_calls": int(bucket["tool_calls"]),
                "tokens_entrada": int(bucket["tokens_entrada"]),
                "tokens_saida": int(bucket["tokens_saida"]),
                "custo_usd": round(bucket["custo_usd"], 6),
            }
        )
    return pd.DataFrame(data)


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


def render_agent_cost_table(
    records: list[dict[str, Any]],
    *,
    title: str = "Custo e latência por agente",
) -> str:
    """HTML table of per-agent instrumentation."""
    df = build_agent_cost_table(records)
    if df.empty:
        df = pd.DataFrame([{"agente": "—", "passos": 0, "latencia_s": 0, "chamadas_llm": 0}])
    return render_comparison_report(
        df,
        status_col="agente",
        title=title,
        subtitle="Soma no run · security e handoff são nós determinísticos (0 LLM).",
        code_columns=frozenset({"agente"}),
    )


def _fmt_rate(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.1%}"


def _fmt_score(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.4f}"


def build_arch_instrumentation_table(
    manifests: dict[str, dict[str, Any]],
    context: EvalContext = "recomendacao",
) -> pd.DataFrame:
    """Compare run instrumentation (cost, latency, tokens, calls) across architectures."""
    rows: list[dict[str, str]] = []
    for arch in ("baseline", "workflow", "multiagent"):
        manifest = manifests.get(arch)
        if not manifest:
            continue
        records = filter_records_by_context(manifest.get("records") or [], context)
        if not records:
            continue
        resumo = summarize_records(records)
        tokens_in = int(resumo.get("tokens_entrada") or 0)
        tokens_out = int(resumo.get("tokens_saida") or 0)
        rows.append(
            {
                "versão": ARCHITECTURE_LABELS.get(arch, arch),
                "casos": str(len(records)),
                "latência média (s)": str(resumo.get("latencia_media_s") or "—"),
                "latência mediana (s)": str(resumo.get("latencia_mediana_s") or "—"),
                "tokens entrada": f"{tokens_in:,}",
                "tokens saída": f"{tokens_out:,}",
                "tokens total": f"{tokens_in + tokens_out:,}",
                "chamadas ao modelo": str(resumo.get("chamadas_llm") or 0),
                "chamadas de ferramentas": str(resumo.get("tool_calls") or 0),
                "custo estimado (USD)": f"${float(resumo.get('custo_estimado_usd') or 0):.4f}",
            }
        )
    if not rows:
        rows.append({"versão": "—", "casos": "0"})
    return pd.DataFrame(rows)


def render_arch_instrumentation_panel(
    manifests: dict[str, dict[str, Any]],
    context: EvalContext = "recomendacao",
    *,
    title: str = "Instrumentação — E1 × E2 × E3",
) -> str:
    """HTML panel comparing operational metadata across architectures."""
    section = CONTEXT_SECTIONS.get(context, {})
    subtitle = (
        f"{section.get('comparacao', '')} · soma nos casos de "
        f"{CONTEXT_LABELS.get(context, context).lower()}"
    )
    df = build_arch_instrumentation_table(manifests, context)
    return render_comparison_report(
        df,
        status_col="versão",
        title=title,
        subtitle=subtitle,
        code_columns=frozenset(),
        show_legend=False,
    )


def build_context_summary_table(
    manifests: dict[str, dict[str, Any]],
    context: EvalContext,
) -> pd.DataFrame:
    """Human-readable summary table for one evaluation context."""
    section = CONTEXT_SECTIONS[context]
    rows: list[dict[str, str]] = []
    arches = [arch for arch in CONTEXT_ARCHITECTURES[context] if arch in manifests]

    for arch in arches:
        block = (manifests[arch].get("resumo_v3") or {}).get("e3_by_context", {}).get(
            context, {}
        )
        row: dict[str, str] = {
            "versão": ARCHITECTURE_LABELS.get(arch, arch),
            "casos avaliados": str(block.get("n") or "—"),
        }
        if context == "recomendacao":
            row["qualidade do ranking"] = _fmt_score(block.get("mean_ndcg_at_5"))
            row["taxa de lista exata"] = _fmt_rate(block.get("aprovado_exact_rate"))
            row["taxa de erro grave"] = _fmt_rate(block.get("grave_error_rate"))
        elif context == "seguranca":
            row["taxa de aprovação"] = _fmt_rate(block.get("pass_rate"))
            row["taxa de vazamento"] = _fmt_rate(block.get("guardrail_hit_rate"))
        elif context == "faq":
            row["similaridade semântica média"] = _fmt_score(
                block.get("mean_semantic_similarity")
            )
            row["limiar de aprovação"] = str(block.get("semantic_threshold") or FAQ_SEMANTIC_THRESHOLD)
            row["taxa de aprovação"] = _fmt_rate(block.get("pass_rate"))
        else:
            row["taxa de roteamento correto"] = _fmt_rate(block.get("routing_pass_rate"))
            by_dest = block.get("by_destination") or {}
            for dest, label in (
                ("recomendação", "acerto em recomendação"),
                ("perguntas frequentes", "acerto em FAQ"),
                ("transbordo", "acerto em transbordo"),
            ):
                dest_block = by_dest.get(dest) or {}
                row[label] = _fmt_rate(dest_block.get("pass_rate"))
        rows.append(row)

    if not rows:
        rows.append({"versão": "—", "casos avaliados": "0"})
    return pd.DataFrame(rows)


def build_context_case_table(
    records: list[dict[str, Any]],
    context: EvalContext,
    *,
    output_column: str = "resposta do sistema",
) -> pd.DataFrame:
    """Per-case detail table with context-specific columns in Portuguese."""
    subset = filter_records_by_context(records, context)
    rows: list[dict[str, Any]] = []
    for record in subset:
        case = record["case"]
        check = record["check"]
        restrict = is_restrict_scope(case["familia"])
        status = final_status(check["aprovado"], restrict)
        row: dict[str, Any] = {
            "caso": case["id"],
            "status_final": status,
            "pergunta": case.get("entrada") or " / ".join(case.get("turns") or []),
            output_column: format_baseline_col(check),
        }
        if context == "recomendacao":
            row["qualidade do ranking"] = check.get("ndcg_at_5")
            row["gravidade do erro"] = check.get("severity")
            row["gabarito"] = format_gabarito_col(case, check)
        elif context == "seguranca":
            row["vazamento detectado"] = bool(
                check.get("pii_hits") or check.get("injection_hits") or check.get("jailbreak_hits")
            )
            row["gabarito"] = format_gabarito_col(case, check)
        elif context == "faq":
            row["similaridade semântica"] = check.get("faq_semantic_similarity")
            row["texto gerado"] = (check.get("answer_text") or "")[:160]
            row["referência"] = (case.get("expected_answer") or "")[:160]
        else:
            row["destino esperado"] = routing_destination(case)
            row["rota executada"] = " > ".join(check.get("agents_route") or [])
            row["status final"] = check.get("status")
        rows.append(row)
    return pd.DataFrame(rows)


def render_context_evaluation_section(
    manifests: dict[str, dict[str, Any]],
    records: list[dict[str, Any]],
    context: EvalContext,
    *,
    output_column: str = "resposta do sistema",
) -> str:
    """Full HTML section: intro, summary table and per-case table for one context."""
    section = CONTEXT_SECTIONS[context]
    summary_df = build_context_summary_table(manifests, context)
    cases_df = build_context_case_table(records, context, output_column=output_column)

    intro = (
        f'<p style="margin:0 0 10px;font-size:14px;line-height:1.55;color:#1f2937;">'
        f'<strong>Pergunta avaliada:</strong> {section["pergunta"]}<br>'
        f'<strong>Comparação:</strong> {section["comparacao"]}<br>'
        f'<strong>Métrica principal:</strong> {section["metrica_principal"]}<br>'
        f'<strong>Casos:</strong> {section["casos"]}'
        f"</p>"
    )
    summary_html = render_comparison_report(
        summary_df,
        status_col="versão",
        title=section["titulo"],
        subtitle=section["comparacao"],
        code_columns=frozenset(),
        show_legend=False,
    )
    instrumentation_html = ""
    if context == "recomendacao" and len(manifests) > 1:
        instrumentation_html = render_arch_instrumentation_panel(
            manifests,
            context,
            title="H.1 — Instrumentação (custo, latência e chamadas)",
        )
    cases_html = render_comparison_report(
        cases_df,
        status_col="status_final",
        title=f"Detalhe por caso — {CONTEXT_LABELS[context]}",
        subtitle=f"{len(cases_df)} casos · resultado individual",
        code_columns=frozenset({"pergunta", "texto gerado", "referência", "rota executada", "gabarito"}),
        show_legend=True,
    )
    return intro + summary_html + instrumentation_html + cases_html


def render_arch_comparison_v3(
    manifests: list[dict[str, Any]],
    *,
    title: str = "Comparação E3 — baseline × workflow × multiagent (recomendação)",
) -> str:
    """Three-column comparison using ``resumo_v3`` scopes."""
    labels = [m.get("architecture_id", f"arch{i}") for i, m in enumerate(manifests)]
    metric_rows = [
        ("e3_overall.mean_ndcg_at_5", "overall mean nDCG@5"),
        ("e3_overall.aprovado_exact_rate", "overall aprovado_exact"),
        ("e3_overall.grave_error_rate", "overall grave_error_rate"),
        ("e3_restrict_core.mean_ndcg_at_5", "restrict_core nDCG@5"),
        ("e3_gap.gap_intentional_pass_rate", "gap_intentional_pass"),
        ("e3_memory.aprovado_exact_rate", "memory aprovado_exact"),
        ("e3_scoring.aprovado_exact_rate", "scoring aprovado_exact"),
        ("e1_rate_overall", "legado e1_rate_overall"),
        ("latencia_mediana_s", "latência mediana (s)"),
        ("chamadas_llm", "chamadas LLM"),
        ("custo_estimado_usd", "custo est. (USD)"),
    ]

    def _dig(resumo: dict[str, Any], dotted: str) -> Any:
        current: Any = resumo
        for part in dotted.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    rows = []
    for dotted, label in metric_rows:
        row: dict[str, Any] = {"métrica": label}
        for label_arch, manifest in zip(labels, manifests, strict=True):
            resumo = manifest.get("resumo_v3") or manifest.get("resumo") or {}
            row[label_arch] = _dig(resumo, dotted)
        rows.append(row)
    df = pd.DataFrame(rows)
    revision = manifests[0].get("golden_revision", "—") if manifests else "—"
    return render_comparison_report(
        df,
        status_col="métrica",
        title=title,
        subtitle=f"golden_revision={revision} · mesmo modelo · mesma sessão",
        code_columns=frozenset(),
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
