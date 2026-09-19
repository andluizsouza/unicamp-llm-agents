"""Deterministic handoff node — fixed template, zero LLM."""

from __future__ import annotations

import time
from typing import Any

from recfair.graphs.multiagent.state import MultiAgentState
from recfair.observability.agent_trace import AgentTrace, append_trace
from recfair.schemas.output import RecFairOutput
from recfair.schemas.routing import AgentMetrics, AgentResult

HANDOFF_PHONE = "0800-000-0000"
HANDOFF_TEXT = (
    "Não consegui resolver isso automaticamente. "
    f"Por favor, fale com o atendimento humano no {HANDOFF_PHONE}."
)


def handoff_node(state: MultiAgentState) -> dict[str, Any]:
    """Return a human-handoff message with the published phone number."""
    start = time.perf_counter()
    prior = [row["agent_id"] for row in (state.get("agent_traces") or [])]
    route = prior + ["handoff"]
    routing = state.get("routing")
    latency = round(time.perf_counter() - start, 4)
    output = RecFairOutput(
        status="handoff",
        halt_reason="completed",
        answer_text=HANDOFF_TEXT,
        handoff_phone=HANDOFF_PHONE,
        agents_route=route,
    )
    trace = AgentTrace(
        agent_id="handoff",
        routing_reason=routing.routing_reason if routing else "handoff",
        plan=list(routing.plan) if routing else ["handoff"],
        replanned=bool(routing.replanned) if routing else False,
        latencia_s=latency,
    )
    last_result = AgentResult(
        agent_id="handoff",
        status="ok",
        payload={"phone": HANDOFF_PHONE},
        metrics=AgentMetrics(latencia_s=latency),
    )
    return {
        "output": output,
        "last_result": last_result,
        "agents_route": route,
        "agent_traces": append_trace(state, trace),
        "step": state.get("step", 0) + 1,
    }
