"""HTML table rendering for eval reports."""

from __future__ import annotations

import pandas as pd

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
