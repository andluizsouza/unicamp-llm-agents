"""Formatting helpers for eval report tables."""

from __future__ import annotations

from typing import Any

from eval.metrics import FAQ_SEMANTIC_THRESHOLD
from recfair.config import HANDOFF_PHONE, OUT_OF_CONTEXT_TEXT


def is_restrict_scope(familia: str) -> bool:
    """True for S_* families (T01–T15)."""
    return familia.startswith("S_")


def gold_diff_label(skus: list[str], gold: list[str]) -> str:
    if not gold:
        return "—"
    if skus == gold:
        return "igual ao gabarito"
    parts: list[str] = []
    only_out = [s for s in skus if s not in gold]
    only_gold = [s for s in gold if s not in skus]
    if only_out:
        parts.append(f"extras na saída: {only_out}")
    if only_gold:
        parts.append(f"faltam do gabarito: {only_gold}")
    if skus and gold and set(skus) == set(gold):
        parts.append("mesmos SKUs, ordem diferente")
    return "; ".join(parts) if parts else "lista diferente"


def format_baseline_col(check: dict[str, Any]) -> str:
    if check.get("status") == "abstention":
        return f"abstention · {check.get('reason')}"
    skus = check.get("skus") or []
    return " → ".join(skus) if skus else "—"


def format_gabarito_col(case: dict[str, Any], check: dict[str, Any]) -> str:
    if case["familia"] == "S_abstain":
        return f"abstention · {case['expected_reason']}"
    gold = check.get("gold") or []
    base = " → ".join(gold) if gold else "—"
    familia = case["familia"]
    if familia == "G_need" and case.get("target_sku"):
        return f"{base} (+ claim {case['target_sku']})"
    if familia == "G_price":
        return f"{base} (+ filtro preço)"
    if familia == "G_stock":
        return f"{base} (+ filtro estoque)"
    if familia == "G_launch":
        return f"{base} (+ flag lançamento)"
    if familia == "G_promo":
        return f"{base} (+ flag promoção)"
    if familia in {"G_faq_ecommerce", "G_faq_revenda"}:
        if case.get("expected_answer"):
            return f"faq · resposta ref. (semântica ≥ {FAQ_SEMANTIC_THRESHOLD})"
        return f"faq · keywords {case.get('expected_keywords')}"
    if familia == "G_routing":
        return f"rota contém {case.get('expected_route')}"
    if familia == "G_out_of_context":
        return f"out_of_context · {OUT_OF_CONTEXT_TEXT[:40]}…"
    if familia == "G_handoff":
        return f"handoff · {HANDOFF_PHONE}"
    return base


def final_status(aprovado: bool, restrict: bool) -> str:
    if aprovado:
        return "sucesso"
    return "erro" if restrict else "erro*"


def recommendation_final_status(check: dict[str, Any], restrict: bool) -> str:
    """Status for H.1 recommendation panels (ADR 0004).

    Uses ``aprovado_exact`` so a case that matches the engine gold is marked
    as success even when legacy ``aprovado`` applies extra RF checks (e.g.
    T14 forbidden SKU present in gold, T38 single-brand diversity).
    """
    if check.get("aprovado_exact"):
        return "sucesso"
    return "erro" if restrict else "erro*"


_E2_SECURITY_FAMILIAS = frozenset({"G_pii", "G_injection", "G_jailbreak"})


def motivo_sucesso(
    case: dict[str, Any],
    check: dict[str, Any],
    *,
    experiment: str = "e1",
) -> str:
    if not check.get("aprovado") or case["familia"].startswith("S_"):
        return ""
    if experiment == "e2":
        if case["familia"] in _E2_SECURITY_FAMILIAS:
            return "acerto inesperado (guardrail previsto para E3)"
        return ""
    return "acerto inesperado no gap (conta em e1_rate_overall)"


def escopo_label(restrict: bool) -> str:
    return "restrito" if restrict else "global"

