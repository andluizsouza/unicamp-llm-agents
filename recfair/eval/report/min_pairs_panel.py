"""Side-by-side HTML for ethics min-pairs (inputs, outputs, parity)."""

from __future__ import annotations

import html
from typing import Any

from eval.ethics import gold_case_for_pair, pair_verdicts
from eval.gold import catalog, gold_for
from eval.report.html import _PANEL, _PANEL_HDR

_DIM_LABELS = {
    "acerto": "acerto",
    "confianca": "confiança",
    "evidencia": "evidência",
    "ressalvas": "ressalvas",
    "ndcg_at_5": "nDCG@5",
}


def render_min_pairs_panel(
    pair_runs: list[dict[str, Any]],
    *,
    pairs_meta: list[dict[str, Any]] | None = None,
) -> str:
    """Catalog each min-pair member with input, output, validity and consistency.

    Without a snapshot, model outputs stay pending and the shared gold stays visible.
    """
    pairs = _display_pairs(pair_runs, pairs_meta)
    if not pairs:
        return (
            f'<div style="{_PANEL}"><div style="{_PANEL_HDR}">'
            '<div style="font-size:1.08rem;font-weight:700;color:#ffffff;">'
            "Catálogo de pares mínimos (exemplos de entrada)</div>"
            '<div style="font-size:12px;color:#e2e8f0;margin-top:5px;">'
            "Nenhum par em `data/golden/min_pairs.json`.</div></div></div>"
        )
    measured = any(_variant_measured(v) for pair in pairs for v in pair.get("variants") or [])
    subtitle = (
        "Cada reformulação mostra os dois lados: entrada completa, saída do modelo, "
        "validade (`verify_case` no ouro compartilhado) e consistência acima do ruído (§D)."
    )
    if not measured:
        subtitle += (
            " Saída do modelo pendente — grave o snapshot com `RUN_FAST=False` "
            "em `eval/fixtures/e4_min_pairs_resilient.json`."
        )
    parts = [
        f'<div style="{_PANEL}">',
        f'<div style="{_PANEL_HDR}">',
        '<div style="font-size:1.08rem;font-weight:700;color:#ffffff;margin:0;">'
        "Catálogo de pares mínimos (exemplos de entrada)</div>",
        f'<div style="font-size:12px;color:#e2e8f0;margin-top:5px;line-height:1.45;">{subtitle}</div>',
        "</div>",
        '<div style="padding:14px 16px;background:#ffffff;">',
    ]
    for pair in pairs:
        parts.append(_render_pair(pair))
    parts.append("</div></div>")
    return "".join(parts)


def _display_pairs(
    pair_runs: list[dict[str, Any]],
    pairs_meta: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    meta_by_id = {pair["pair_id"]: pair for pair in (pairs_meta or [])}
    source = pair_runs or list(pairs_meta or [])
    out: list[dict[str, Any]] = []
    for pair in source:
        meta = meta_by_id.get(pair.get("pair_id")) or {}
        row = dict(pair)
        row["note"] = pair.get("note") or meta.get("note")
        row["_meta"] = meta or pair
        if meta and not row.get("variants"):
            row["variants"] = meta.get("variants") or []
        out.append(row)
    return out


def _render_pair(pair: dict[str, Any]) -> str:
    pair_id = str(pair.get("pair_id") or "—")
    axis = pair.get("axis") or "—"
    layer = pair.get("layer") or "—"
    note = pair.get("note") or ""
    gold = _gold_line(pair)
    groups = _by_reformulation(pair.get("variants") or [])
    verdict_by_ref = {v.get("reformulation"): v for v in pair_verdicts(pair)}
    blocks = [
        '<section style="border:1px solid #d1d5db;border-radius:10px;margin:0 0 16px;overflow:hidden;">',
        '<header style="background:#f8fafc;padding:12px 14px;border-bottom:1px solid #e5e7eb;">',
        f'<div style="font-weight:700;color:#0f172a;font-size:15px;">{_esc(pair_id)}'
        f' <span style="font-weight:500;color:#475569;">· {_esc(axis)} · {_esc(layer)}</span></div>',
    ]
    if note:
        blocks.append(
            f'<div style="margin-top:4px;color:#334155;font-size:13px;line-height:1.45;">{_esc(note)}</div>'
        )
    blocks.append(
        '<div style="margin-top:8px;font-size:12px;color:#1e293b;line-height:1.45;">'
        f"<strong>Ouro compartilhado:</strong> {_esc(gold)}</div>"
        "</header>"
    )
    for reformulation, members in groups:
        verdict = verdict_by_ref.get(reformulation)
        blocks.append(
            '<div style="padding:12px 14px;border-top:1px solid #e5e7eb;">'
            f'<div style="font-size:12px;font-weight:700;letter-spacing:0.04em;'
            f'text-transform:uppercase;color:#475569;margin-bottom:8px;">'
            f"Reformulação {_esc(reformulation)}</div>"
            '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;">'
        )
        for member in members:
            blocks.append(_render_member(member))
        blocks.append("</div>")
        blocks.append(_render_consistency(members, verdict))
        blocks.append("</div>")
    blocks.append("</section>")
    return "".join(blocks)


def _render_member(variant: dict[str, Any]) -> str:
    label = variant.get("label") or "—"
    member_id = variant.get("id") or ""
    title = f"{label} · {member_id}" if member_id else str(label)
    entrada = variant.get("entrada") or "—"
    saida = _output_text(variant)
    validade = _validade(variant)
    validade_html = (
        _badge(validade, _validade_kind(validade)) if validade else _badge("pendente", "muted")
    )
    saida_html = (
        f'<div style="white-space:pre-wrap;word-break:break-word;">{_esc(saida)}</div>'
        if saida
        else '<div style="color:#6b7280;">Saída do modelo ainda não gravada neste snapshot.</div>'
    )
    return (
        '<article style="border:1px solid #e5e7eb;border-radius:8px;padding:10px 12px;background:#ffffff;">'
        f'<div style="font-weight:700;color:#111827;margin-bottom:8px;">{_esc(title)}</div>'
        '<div style="font-size:11px;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;'
        'color:#6b7280;">Entrada</div>'
        f'<div style="margin:4px 0 10px;color:#111827;line-height:1.45;white-space:pre-wrap;'
        f'word-break:break-word;">{_esc(entrada)}</div>'
        '<div style="font-size:11px;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;'
        'color:#6b7280;">Saída</div>'
        f'<div style="margin:4px 0 10px;color:#111827;font-size:13px;line-height:1.45;">{saida_html}</div>'
        f'<div style="font-size:13px;">Validade {validade_html}</div>'
        "</article>"
    )


def _render_consistency(
    members: list[dict[str, Any]],
    verdict: dict[str, Any] | None,
) -> str:
    measured = all(_variant_measured(member) for member in members) and len(members) >= 2
    if not measured:
        label, kind = "consistência pendente (sem saída dos dois lados)", "muted"
        extra = ""
    elif verdict and verdict.get("relevante"):
        label = "diferença relevante: " + _format_deltas(verdict)
        kind = "warn"
        extra = _sku_list_note(members)
    else:
        label = "paridade (dentro do ruído)"
        kind = "ok"
        extra = _sku_list_note(members)
    extra_html = (
        f'<span style="margin-left:8px;color:#374151;font-size:12px;">{_esc(extra)}</span>'
        if extra
        else ""
    )
    return (
        '<div style="margin-top:10px;font-size:13px;color:#111827;">'
        f"<strong>Consistência:</strong> {_badge(label, kind)}{extra_html}</div>"
    )


def _by_reformulation(
    variants: list[dict[str, Any]],
) -> list[tuple[Any, list[dict[str, Any]]]]:
    groups: dict[Any, list[dict[str, Any]]] = {}
    for variant in variants:
        groups.setdefault(variant.get("reformulation"), []).append(variant)
    return sorted(groups.items(), key=lambda item: str(item[0]))


def _variant_measured(variant: dict[str, Any]) -> bool:
    return bool(variant.get("media") or variant.get("saida"))


def _gold_line(pair: dict[str, Any]) -> str:
    meta = pair.get("_meta") or {}
    skus: list[str] = []
    if meta.get("familia") or meta.get("category") or meta.get("pair_id"):
        try:
            skus = list(gold_for(gold_case_for_pair(meta if meta.get("pair_id") else pair)))
        except KeyError, TypeError:
            skus = []
    if not skus:
        for variant in pair.get("variants") or []:
            skus = list((variant.get("saida") or {}).get("gold") or [])
            if skus:
                break
    text = _format_skus(skus)
    target = meta.get("target_sku") or pair.get("target_sku")
    if target:
        text = f"{text} · alvo {target}"
    return text


def _format_member_skus(saida: dict[str, Any]) -> str:
    skus = list(saida.get("skus") or [])
    nomes = list(saida.get("nomes") or [])
    cat = catalog()
    parts: list[str] = []
    for index, sku in enumerate(skus):
        name = str(nomes[index]).strip() if index < len(nomes) and nomes[index] else ""
        if not name:
            name = str((cat.get(sku) or {}).get("name_sku") or "").strip()
        parts.append(f"{sku} — {name}" if name else str(sku))
    return " · ".join(parts)


def _format_skus(skus: list[str]) -> str:
    if not skus:
        return "—"
    cat = catalog()
    parts: list[str] = []
    for sku in skus:
        name = str((cat.get(sku) or {}).get("name_sku") or "").strip()
        parts.append(f"{sku} — {name}" if name else str(sku))
    return " · ".join(parts)


def _output_text(variant: dict[str, Any]) -> str:
    saida = variant.get("saida") or {}
    if not saida:
        return ""
    skus = list(saida.get("skus") or [])
    body = (
        _format_member_skus(saida) if skus else (str(saida.get("answer_text") or "").strip() or "—")
    )
    bits = [str(saida.get("status") or "")]
    if saida.get("degraded"):
        bits.append("degradada")
    halt = saida.get("halt_reason")
    if halt and halt != "completed":
        bits.append(str(halt))
    head = " · ".join(bit for bit in bits if bit)
    return f"{head}\n{body}" if head else body


def _validade(variant: dict[str, Any]) -> str | None:
    if not _variant_measured(variant):
        return None
    saida = variant.get("saida") or {}
    runs = variant.get("runs") or []
    if "aprovado" in saida and len(runs) <= 1:
        return "válido" if saida["aprovado"] else "inválido"
    acerto = (variant.get("media") or {}).get("acerto")
    if acerto is None and "aprovado" in saida:
        return "válido" if saida["aprovado"] else "inválido"
    if acerto is None:
        return None
    score = float(acerto)
    if score >= 1:
        return "válido"
    if score <= 0:
        return "inválido"
    return f"parcial ({score:.2f})"


def _validade_kind(label: str) -> str:
    if label == "válido":
        return "ok"
    if label == "inválido":
        return "bad"
    if label.startswith("parcial"):
        return "warn"
    return "muted"


def _format_deltas(verdict: dict[str, Any]) -> str:
    flags = verdict.get("flags") or {}
    deltas = verdict.get("deltas") or {}
    bits: list[str] = []
    for key, flagged in flags.items():
        if not flagged:
            continue
        name = _DIM_LABELS.get(key, str(key))
        delta = deltas.get(key)
        if isinstance(delta, (int, float)):
            bits.append(f"{name} {delta:+.3f}")
        else:
            bits.append(name)
    return ", ".join(bits) if bits else "dimensões divergentes"


def _sku_list_note(members: list[dict[str, Any]]) -> str:
    lists = [list((member.get("saida") or {}).get("skus") or []) for member in members[:2]]
    if len(lists) < 2 or not lists[0] or not lists[1]:
        return ""
    left, right = lists
    if left == right:
        return "Listas de SKU iguais."
    if set(left) == set(right):
        return "Mesmos SKUs, ordem diferente."
    return "Listas de SKU diferem."


def _badge(label: str, kind: str) -> str:
    palette = {
        "ok": ("#d1e7dd", "#0a3622", "#a3cfbb"),
        "bad": ("#f8d7da", "#58151c", "#f1aeb5"),
        "warn": ("#fff3cd", "#664d03", "#ffe69c"),
        "muted": ("#e9ecef", "#343a40", "#ced4da"),
    }
    bg, fg, border = palette.get(kind, palette["muted"])
    return (
        '<span style="display:inline-block;padding:3px 10px;border-radius:999px;'
        f"background:{bg};color:{fg};border:1px solid {border};"
        f'font-weight:600;font-size:12px;">{_esc(label)}</span>'
    )


def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
