"""Deterministic demos for the E4 notebook (no LLM)."""

from __future__ import annotations

import random
from typing import Any

from recfair.harness.context import HarnessSettings, harness_scope
from recfair.harness.degrade import tool_error_output
from recfair.harness.retry import TransientError, call_with_retry
from recfair.harness.unstable import maybe_fail
from recfair.harness.verify_output import (
    apply_silent_failure_checks,
    verify_confidence,
    verify_evidence,
)
from recfair.schemas.output import RecFairOutput, RecommendationItem
from recfair.schemas.routing import AgentResult, RoutingDecision


def demo_containment(
    *,
    failure_prob: float = 0.4,
    n_calls: int = 10,
    seed: int = 7,
) -> dict[str, Any]:
    """Unstable tool (p known) + retry + labelled degrade. AP7 pattern.

    Args:
        failure_prob: Chance each inner call raises ``FonteIndisponivel``.
        n_calls: How many top-level protected calls to run.
        seed: RNG seed for reproducibility.

    Returns:
        Counts of success, retry recoveries, and degraded outcomes.
    """
    rng = random.Random(seed)
    recovered = 0
    degraded = 0
    ok = 0
    traces: list[dict[str, Any]] = []
    settings = HarnessSettings(enabled=True, inject_failure_prob=failure_prob, max_retries=3)
    with harness_scope(settings):
        for index in range(n_calls):
            attempts = {"n": 0}

            def _unstable() -> str:
                attempts["n"] += 1
                maybe_fail(rng=rng)
                return "ok"

            try:
                call_with_retry(_unstable, sleep=lambda _s: None, jitter=False)
                ok += 1
                if attempts["n"] > 1:
                    recovered += 1
                traces.append({"i": index, "status": "ok", "tries": attempts["n"]})
            except TransientError:
                degraded += 1
                traces.append(
                    {
                        "i": index,
                        "status": "degraded",
                        "output": tool_error_output().halt_reason,
                    }
                )

    return {
        "failure_prob": failure_prob,
        "n_calls": n_calls,
        "ok": ok,
        "degraded": degraded,
        "degraded_identifies_as_partial": True,
        "halt_on_degrade": "tool_error",
        "traces": traces,
        "recovered": recovered,
    }


def demo_silent_checks() -> dict[str, Any]:
    """Show both silent-failure verifiers catching bad outputs."""
    invented = RecFairOutput(
        status="recommendation",
        halt_reason="completed",
        items=[
            RecommendationItem(
                sku="ZZZZZZ",
                name="Inventado",
                brand="X",
                category="cabelos",
                units_7d=1,
                citations=["beneficios: texto que não existe na fonte"],
            )
            for _ in range(5)
        ],
    )
    evidence_issues = verify_evidence(invented, catalog={})

    faq = RecFairOutput(
        status="faq",
        halt_reason="completed",
        answer_text="O prazo é 3 dias úteis.",
        citations=[],
    )
    routing = RoutingDecision(
        domain="faq",
        skill="skill_faq",
        plan=["skill_faq"],
        routing_reason="faq",
        confidence=0.95,
    )
    last = AgentResult(agent_id="faq", status="ok")
    confidence_issues = verify_confidence(faq, routing=routing, last_result=last)
    converted = apply_silent_failure_checks(faq, routing=routing, last_result=last)
    prefix = converted.answer_text and converted.answer_text.startswith("[Resposta parcial]")
    return {
        "evidence_issues": evidence_issues,
        "confidence_issues": confidence_issues,
        "converted_status": converted.status,
        "converted_degraded": converted.degraded,
        "converted_halt": converted.halt_reason,
        "user_sees_partial": bool(prefix),
    }
