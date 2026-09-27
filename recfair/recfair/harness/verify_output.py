"""Convert silent failures into detectable (noisy) ones."""

from __future__ import annotations

from typing import Any

from recfair.config import HANDOFF_PHONE
from recfair.data.catalog import catalog_by_sku
from recfair.data.claims import claims_by_sku
from recfair.harness.context import current_settings
from recfair.harness.degrade import DEGRADED_PREFIX, label_degraded
from recfair.schemas.output import RecFairOutput
from recfair.schemas.routing import AgentResult, RoutingDecision

_DOMAIN_AGENT = {
    "recommendation": "recommendation",
    "faq": "faq",
    "handoff": "handoff",
    "out_of_context": "out_of_context",
}


def _norm(text: str) -> str:
    return " ".join((text or "").lower().split())


def verify_evidence(
    output: RecFairOutput,
    *,
    catalog: dict[str, Any] | None = None,
    faq_evidence: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Check that cited evidence exists in the catalog, claims, or FAQ chunks.

    Returns:
        Issue codes. Empty means the check passed.
    """
    issues: list[str] = []
    cat = catalog if catalog is not None else catalog_by_sku()
    claims = claims_by_sku()

    for item in output.items:
        if item.sku not in cat:
            issues.append(f"invented_sku:{item.sku}")
            continue
        blob = " ".join((claims.get(item.sku) or {}).values())
        for cite in item.citations or []:
            body = cite.split(":", 1)[-1].strip()
            if body and _norm(body) not in _norm(blob) and _norm(cite) not in _norm(blob):
                issues.append(f"citation_not_in_claims:{item.sku}")

    if output.status == "faq":
        excerpts = [_norm(str(hit.get("excerpt") or "")) for hit in (faq_evidence or [])]
        joined = " ".join(excerpts)
        for cite in output.citations or []:
            body = _norm(cite.split(":", 1)[-1] if ":" in cite else cite)
            if body and body[:80] not in joined and not any(body[:80] in ex for ex in excerpts):
                issues.append("citation_not_in_faq")
                break
        answer = _norm(output.answer_text or "")
        overlap = any(ex[:40] in answer or answer[:40] in ex for ex in excerpts if ex)
        if answer and excerpts and not overlap:
            tokens = [token for token in answer.split()[:6] if len(token) > 4]
            if len(answer) > 40 and all(token not in joined for token in tokens):
                issues.append("answer_not_grounded")

    return list(dict.fromkeys(issues))


def verify_confidence(
    output: RecFairOutput,
    *,
    routing: RoutingDecision | None = None,
    last_result: AgentResult | None = None,
) -> list[str]:
    """Check that declared confidence and specialist scope match the evidence.

    Returns:
        Issue codes. Empty means the check passed.
    """
    issues: list[str] = []
    threshold = current_settings().high_confidence
    if routing is not None and routing.confidence >= threshold:
        has_evidence = bool(output.citations) or any(item.citations for item in output.items)
        if output.status == "faq" and not has_evidence:
            issues.append("high_confidence_without_evidence")
        if output.status == "recommendation" and not has_evidence:
            issues.append("high_confidence_without_evidence")

    if routing is not None and last_result is not None:
        expected = _DOMAIN_AGENT.get(routing.domain)
        allowed = {expected, "handoff", "out_of_context", "security", "supervisor"}
        if expected and last_result.agent_id not in allowed and last_result.status == "ok":
            issues.append(f"scope_mismatch:{last_result.agent_id}!={routing.domain}")

    return list(dict.fromkeys(issues))


def apply_silent_failure_checks(
    output: RecFairOutput,
    *,
    routing: RoutingDecision | None = None,
    last_result: AgentResult | None = None,
    faq_evidence: list[dict[str, Any]] | None = None,
    catalog: dict[str, Any] | None = None,
) -> RecFairOutput:
    """Run both silent-failure checks and convert hits into a labelled handoff.

    Args:
        output: Candidate response after citation fill.
        routing: Supervisor decision, if any.
        last_result: Last specialist result.
        faq_evidence: Retrieved FAQ chunks.
        catalog: Optional catalog map (tests inject a stub).

    Returns:
        The original output, or a degraded handoff when a check fires.
    """
    issues = [
        *verify_evidence(output, catalog=catalog, faq_evidence=faq_evidence),
        *verify_confidence(output, routing=routing, last_result=last_result),
    ]
    if not issues:
        return output

    reason = ",".join(issues[:4])
    if output.status == "handoff" and output.degraded:
        return output.model_copy(update={"degraded_reason": reason})

    handoff = RecFairOutput(
        status="handoff",
        halt_reason="degraded",
        degraded=True,
        degraded_reason=reason,
        answer_text=(
            f"{DEGRADED_PREFIX}Detectei uma inconsistência entre a resposta e a fonte "
            f"(verificação ativa). Fale com o atendimento humano no {HANDOFF_PHONE}."
        ),
        handoff_phone=HANDOFF_PHONE,
        agents_route=[*(output.agents_route or []), "verify"],
        citations=list(output.citations or []),
    )
    return label_degraded(handoff, reason=reason)
