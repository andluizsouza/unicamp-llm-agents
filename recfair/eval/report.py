"""Notebook report tables and HTML panels."""

from __future__ import annotations

from typing import Any

import pandas as pd

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
) -> pd.DataFrame:
    """Build per-case comparison table from runner records."""
    rows = []
    for rec in records:
        case = rec["case"]
        check = rec["check"]
        restrict = is_restrict_scope(case["familia"])
        motivo = motivo_sucesso(case, check) or diagnose_failure(case, check)
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


def _status_badge(status: str) -> str:
    palette = {
        "sucesso": ("#d1e7dd", "#0a3622", "#a3cfbb"),
        "erro": ("#f8d7da", "#58151c", "#f1aeb5"),
        "erro*": ("#fff3cd", "#664d03", "#ffe69c"),
    }
    bg, fg, border = palette.get(status, ("#e9ecef", "#343a40", "#ced4da"))
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
    if col == "status_final":
        return f'<td style="{base}">{_status_badge(status)}</td>'
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
) -> str:
    accent = {"sucesso": "#198754", "erro": "#dc3545", "erro*": "#fd7e14"}
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
        st = str(row.get(status_col, ""))
        stripe = "#f9fafb" if i % 2 else "#ffffff"
        border_color = accent.get(st, "#9ca3af")
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
    parts.append(
        '<div style="display:flex;flex-wrap:wrap;gap:14px;padding:10px 14px 12px;font-size:12px;'
        'color:#374151;background:#f9fafb;border-top:1px solid #e5e7eb;">'
        '<span style="color:#111827;"><span style="display:inline-block;width:10px;height:10px;border-radius:2px;'
        'background:#198754;margin-right:6px;"></span>sucesso (restrito ou gap acertado)</span>'
        '<span style="color:#111827;"><span style="display:inline-block;width:10px;height:10px;border-radius:2px;'
        'background:#dc3545;margin-right:6px;"></span>erro (restrito)</span>'
        '<span style="color:#111827;"><span style="display:inline-block;width:10px;height:10px;border-radius:2px;'
        'background:#fd7e14;margin-right:6px;"></span>erro* (gap falhou)</span>'
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
) -> str:
    return (
        f'<div style="{_PANEL}">'
        f'<div style="{_PANEL_HDR}">'
        f'<div style="font-size:1.08rem;font-weight:700;color:#ffffff;margin:0;'
        f'letter-spacing:-0.01em;">{title}</div>'
        f'<div style="font-size:12px;color:#e2e8f0;margin-top:5px;line-height:1.4;">'
        f"{subtitle}</div>"
        "</div>"
        f'<div style="overflow-x:auto;background:#ffffff;">'
        f"{_render_table_body(df, status_col, code_columns=code_columns)}</div>"
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
    restrict_ok = restrict_ok if restrict_ok is not None else resumo[f"{metric_prefix}_rate_restrict_n"]
    restrict_n = restrict_n if restrict_n is not None else resumo[f"{metric_prefix}_rate_restrict_d"]
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
        "tokens_entrada_media": round(float(tok_in_series.mean()), 1) if len(tok_in_series) else None,
        "tokens_saida_media": round(float(tok_out_series.mean()), 1) if len(tok_out_series) else None,
        "custo_estimado_usd": round(estimate_llm_cost_usd(tok_in, tok_out), 6),
        "nota_custo": (
            f"${USD_PER_1M_INPUT_TOKENS}/1M in, ${USD_PER_1M_OUTPUT_TOKENS}/1M out (thinking incl.)"
        ),
    }


def _manifest_resumo(manifest: dict[str, Any]) -> dict[str, Any]:
    """Return resumo, recomputing from records when needed for older runs."""
    resumo = manifest.get("resumo", {})
    records = manifest.get("records")
    if records and (
        "tokens_entrada_media" not in resumo or "tokens_saida_media" not in resumo
    ):
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
            if key.endswith("_rate_restrict") or key.endswith("_rate_scoring") or key.endswith(
                "_rate_memory"
            ) or key.endswith("_rate_overall"):
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
    panel_subtitle = subtitle or (
        f"golden_revision={revision} · mesmo modelo · mesma sessão"
    )
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
