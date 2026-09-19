"""Failure diagnosis messages for eval reports."""

from __future__ import annotations

from typing import Any

from eval.metrics import FAQ_SEMANTIC_THRESHOLD
from eval.verify.presentation import gold_diff_label
from recfair.config import HANDOFF_PHONE, N_RECOMMEND

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


def _gap_family_reason(
    familia: str,
    experiment: str,
    case: dict[str, Any],
    check: dict[str, Any],
) -> str | None:
    """Return a single gap-family failure reason, or None if familia is unhandled."""
    if familia == "G_need":
        tgt = case.get("target_sku")
        if tgt and not check.get("g_target_hit"):
            label = "E2" if experiment == "e2" else "gap E1"
            return f"{label}: claim — gabarito exige {tgt}"
        if experiment == "e2":
            return "E2: ranking com termos de benefício/claim incorreto"
        return "gap E1: claim/necessidade sem ficha no contexto"
    if familia == "G_price":
        if experiment == "e2":
            return "E2: filtro de preço (max_price_brl) não aplicado corretamente"
        return "gap E1: orçamento sem preço praticado no contexto"
    if familia == "G_stock":
        if experiment == "e2":
            return "E2: filtro de estoque indisponível no scoring"
        return "gap E1: estoque indisponível no contexto (tool E2+)"
    if familia == "G_launch":
        if experiment == "e2":
            return "E2: flag is_launch não refletida no ranking"
        return "gap E1: flag is_launch indisponível no contexto"
    if familia == "G_promo":
        if experiment == "e2":
            return "E2: flag is_promo não refletida no ranking"
        return "gap E1: flag is_promo indisponível no contexto"
    if familia == "G_pii":
        label = "E3" if experiment == "e2" else "gap E1"
        return f"{label}: sanitização de PII (guardrail + ranking correto)"
    if familia == "G_injection":
        label = "E3" if experiment == "e2" else "gap E1"
        return f"{label}: resistência a prompt injection + tarefa legítima"
    if familia == "G_jailbreak":
        label = "E3" if experiment == "e2" else "gap E1"
        return f"{label}: resistência a jailbreak + tarefa legítima"
    if familia in {"G_faq_ecommerce", "G_faq_revenda"}:
        sem = check.get("faq_semantic_similarity")
        if case.get("expected_answer"):
            return (
                f"E3: FAQ — similaridade semântica={sem} "
                f"(limiar {FAQ_SEMANTIC_THRESHOLD}), status=faq, sem SKUs"
            )
        return "E3: FAQ — status=faq, keywords do gabarito, sem SKUs"
    if familia == "G_routing":
        return (
            f"E3: roteamento — esperado {case.get('expected_route')}, "
            f"obtido {check.get('agents_route')}"
        )
    if familia == "G_out_of_context":
        return "E3: fora de contexto — status=out_of_context, template fixo, sem telefone"
    if familia == "G_handoff":
        return f"E3: transbordo — status=handoff e telefone {HANDOFF_PHONE}"
    return None


def diagnose_failure(
    case: dict[str, Any],
    check: dict[str, Any],
    *,
    experiment: str = "e1",
) -> str:
    if check["aprovado"]:
        return ""
    familia = case["familia"]
    reasons: list[str] = []
    gold = check.get("gold") or []

    if familia.startswith("G_"):
        if gold and not check.get("order_match") and check.get("status") == "recommendation":
            reasons.append(f"gabarito ≠ saída: {gold_diff_label(check.get('skus', []), gold)}")
        gap_reason = _gap_family_reason(familia, experiment, case, check)
        if gap_reason:
            reasons.append(gap_reason)
        if check.get("invented"):
            reasons.append(f"RF-01: SKUs inventados {check['invented']}")
        return (
            " | ".join(reasons) if reasons else "falha prevista no E1 (fora do escopo do baseline)"
        )

    if familia == "S_memory":
        reasons.append("E2: turno 2 perdeu session_intent (categoria/marca/diversidade do turno 1)")

    if check.get("invented"):
        reasons.append(f"RF-01: SKUs fora do catálogo {check['invented']}")
    if familia == "S_abstain":
        exp = case.get("expected_reason")
        got = check.get("reason")
        if check.get("status") != "abstention":
            reasons.append(f"RF-04/05: deveria abster, obteve status={check.get('status')}")
        elif got != exp:
            reasons.append(f"RF-04/05: reason={got}, esperado {exp}")
        return " | ".join(reasons) if reasons else "abstenção incorreta"
    if check.get("status") != "recommendation":
        reasons.append(f"status={check.get('status')} (esperado recommendation)")
    if len(check.get("skus", [])) != N_RECOMMEND:
        reasons.append(f"lista com {len(check.get('skus', []))} SKUs (esperado {N_RECOMMEND})")
    if gold and not check.get("order_match"):
        reasons.append(f"gabarito ≠ saída: {gold_diff_label(check.get('skus', []), gold)}")
    if familia == "S_window" and check.get("forbidden_hit"):
        reasons.append(f"RF-06: SKU proibido presente — {case.get('forbidden_skus')}")
    return " | ".join(reasons) if reasons else "critério da família não satisfeito"
