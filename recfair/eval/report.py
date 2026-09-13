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


def build_results_table(records: list[dict[str, Any]]) -> pd.DataFrame:
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
                "baseline": format_baseline_col(check),
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


def _fmt_cell(col: str, text: str, status: str) -> str:
    base = "padding:10px 12px;border-bottom:1px solid #e9ecef;color:#212529;vertical-align:top;"
    if col == "status_final":
        return f'<td style="{base}">{_status_badge(status)}</td>'
    if col in {"baseline", "gabarito"}:
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


def _render_table_body(df: pd.DataFrame, status_col: str = "status_final") -> str:
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
                parts.append(_fmt_cell(col, text, st))
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
_PANEL_HDR = (
    "background:#1e293b;color:#f8fafc;padding:14px 18px;"
    "border-bottom:2px solid #334155;"
)


def render_comparison_report(df: pd.DataFrame, status_col: str = "status_final") -> str:
    return (
        f'<div style="{_PANEL}">'
        f'<div style="{_PANEL_HDR}">'
        '<div style="font-size:1.08rem;font-weight:700;color:#ffffff;margin:0;'
        'letter-spacing:-0.01em;">Baseline × gabarito (golden-set)</div>'
        '<div style="font-size:12px;color:#e2e8f0;margin-top:5px;line-height:1.4;">'
        "Comparação determinística: mesmos SKUs e mesma ordem = sucesso.</div>"
        "</div>"
        f'<div style="overflow-x:auto;background:#ffffff;">{_render_table_body(df, status_col)}</div>'
        "</div>"
    )


def render_metrics_panel(
    resumo: dict[str, Any],
    restrict_ok: int,
    restrict_n: int,
    overall_ok: int,
    overall_n: int,
) -> str:
    rb = lambda ok, n: f"{ok}/{n} ({100 * ok / n:.1f}%)" if n else "—"
    return (
        f'<div style="{_PANEL}max-width:640px;">'
        f'<div style="{_PANEL_HDR}">'
        '<div style="font-size:1.08rem;font-weight:700;color:#ffffff;margin:0;">'
        "Métricas consolidadas</div>"
        '<div style="font-size:12px;color:#e2e8f0;margin-top:5px;">'
        "Run do baseline V1</div>"
        "</div>"
        '<table style="border-collapse:collapse;width:100%;background:#ffffff;color:#111827;">'
        f'<tr><td style="padding:11px 16px;border-bottom:1px solid #e5e7eb;background:#f9fafb;color:#111827;">'
        "<b>e1_rate_restrict</b><br>"
        '<small style="color:#4b5563;">T01–T15 · baseline deve acertar</small></td>'
        f'<td style="padding:11px 16px;border-bottom:1px solid #e5e7eb;font-size:1.15em;color:#111827;">'
        f"<b>{rb(restrict_ok, restrict_n)}</b></td></tr>"
        f'<tr><td style="padding:11px 16px;border-bottom:1px solid #e5e7eb;background:#f9fafb;color:#111827;">'
        "<b>e1_rate_overall</b><br>"
        '<small style="color:#4b5563;">T01–T30 · T16–T30 = gaps G</small></td>'
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


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate E1 metrics from runner records."""
    df = pd.DataFrame(
        [
            {
                "aprovado": r["check"]["aprovado"],
                "restrict": is_restrict_scope(r["case"]["familia"]),
                "latencia_s": r["metrics"]["latencia_s"],
                "tokens_entrada": r["metrics"].get("tokens_entrada"),
                "tokens_saida": r["metrics"].get("tokens_saida"),
                "chamadas_llm": r["metrics"]["chamadas_llm"],
            }
            for r in records
        ]
    )
    restrict_df = df[df["restrict"]]
    n_restrict_ok = int(restrict_df["aprovado"].sum())
    n_restrict = len(restrict_df)
    n_overall_ok = int(df["aprovado"].sum())
    n_overall = len(df)
    tok_in = pd.to_numeric(df["tokens_entrada"], errors="coerce").fillna(0).sum()
    tok_out = pd.to_numeric(df["tokens_saida"], errors="coerce").fillna(0).sum()
    lat = pd.to_numeric(df["latencia_s"], errors="coerce")
    from recfair.config import USD_PER_1M_INPUT_TOKENS, USD_PER_1M_OUTPUT_TOKENS
    from recfair.observability.cost import estimate_llm_cost_usd

    return {
        "e1_rate_restrict": round(n_restrict_ok / n_restrict, 4) if n_restrict else None,
        "e1_rate_restrict_n": n_restrict_ok,
        "e1_rate_restrict_d": n_restrict,
        "e1_rate_overall": round(n_overall_ok / n_overall, 4) if n_overall else None,
        "e1_rate_overall_n": n_overall_ok,
        "e1_rate_overall_d": n_overall,
        "latencia_mediana_s": round(float(lat.median()), 2) if len(lat) else None,
        "latencia_media_s": round(float(lat.mean()), 2) if len(lat) else None,
        "chamadas_llm": int(df["chamadas_llm"].sum()) if len(df) else 0,
        "tokens_entrada": int(tok_in),
        "tokens_saida": int(tok_out),
        "custo_estimado_usd": round(estimate_llm_cost_usd(tok_in, tok_out), 6),
        "nota_custo": (
            f"${USD_PER_1M_INPUT_TOKENS}/1M in, ${USD_PER_1M_OUTPUT_TOKENS}/1M out (thinking incl.)"
        ),
    }
