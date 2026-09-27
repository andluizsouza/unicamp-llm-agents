"""Graceful degradation: partial, labelled responses instead of silence."""

from __future__ import annotations

from recfair.config import HANDOFF_PHONE
from recfair.graphs.multiagent.nodes.handoff import HANDOFF_TEXT
from recfair.schemas.output import HaltReason, RecFairOutput

DEGRADED_PREFIX = "[Resposta parcial] "


def label_degraded(
    output: RecFairOutput,
    *,
    reason: str,
    halt_reason: HaltReason = "degraded",
) -> RecFairOutput:
    """Mark an existing output as degraded and identify it to the user.

    Args:
        output: Structured response to annotate.
        reason: Machine-readable cause (also stored on ``degraded_reason``).
        halt_reason: Halt code written on the contract.

    Returns:
        Copy of ``output`` with ``degraded=True`` and a labelled ``answer_text``.
    """
    text = output.answer_text or HANDOFF_TEXT
    if not text.startswith(DEGRADED_PREFIX):
        text = DEGRADED_PREFIX + text
    route = list(output.agents_route or [])
    if "verify" not in route:
        route = [*route, "verify"]
    return output.model_copy(
        update={
            "degraded": True,
            "degraded_reason": reason,
            "halt_reason": halt_reason,
            "answer_text": text,
            "agents_route": route,
        }
    )


def timeout_output(*, agents_route: list[str] | None = None) -> RecFairOutput:
    """Handoff produced when an operation deadline elapsed."""
    return RecFairOutput(
        status="handoff",
        halt_reason="timeout",
        degraded=True,
        degraded_reason="timeout",
        answer_text=(
            f"{DEGRADED_PREFIX}A consulta excedeu o tempo limite. "
            f"Fale com o atendimento humano no {HANDOFF_PHONE}."
        ),
        handoff_phone=HANDOFF_PHONE,
        agents_route=list(agents_route or ["verify"]),
    )


def tool_error_output(
    *,
    reason: str = "tool_error",
    agents_route: list[str] | None = None,
) -> RecFairOutput:
    """Handoff produced when a tool kept failing after retries."""
    return RecFairOutput(
        status="handoff",
        halt_reason="tool_error",
        degraded=True,
        degraded_reason=reason,
        answer_text=(
            f"{DEGRADED_PREFIX}Não consegui consultar a fonte agora. "
            f"Fale com o atendimento humano no {HANDOFF_PHONE}."
        ),
        handoff_phone=HANDOFF_PHONE,
        agents_route=list(agents_route or ["verify"]),
    )
