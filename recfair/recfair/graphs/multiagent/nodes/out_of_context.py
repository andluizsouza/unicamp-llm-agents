"""Deterministic out-of-context node — fixed redirect template, zero LLM."""

from __future__ import annotations

import time
from typing import Any

from recfair.config import OUT_OF_CONTEXT_TEXT
from recfair.graphs.multiagent.node_helpers import agents_route
from recfair.graphs.multiagent.state import MultiAgentState
from recfair.observability.agent_trace import AgentTrace, append_trace
from recfair.schemas.output import RecFairOutput
from recfair.schemas.routing import AgentMetrics, AgentResult


def out_of_context_node(state: MultiAgentState) -> dict[str, Any]:
    """Return a friendly scope redirect without human handoff."""
    start = time.perf_counter()
    route = agents_route(state, "out_of_context")
    routing = state.get("routing")
    latency = round(time.perf_counter() - start, 4)
    output = RecFairOutput(
        status="out_of_context",
        halt_reason="completed",
        answer_text=OUT_OF_CONTEXT_TEXT,
        agents_route=route,
    )
    trace = AgentTrace(
        agent_id="out_of_context",
        routing_reason=routing.routing_reason if routing else "out_of_context",
        plan=list(routing.plan) if routing else ["out_of_context"],
        replanned=bool(routing.replanned) if routing else False,
        latencia_s=latency,
    )
    last_result = AgentResult(
        agent_id="out_of_context",
        status="ok",
        payload={"redirect": True},
        metrics=AgentMetrics(latencia_s=latency),
    )
    return {
        "output": output,
        "last_result": last_result,
        "agents_route": route,
        "agent_traces": append_trace(state, trace),
        "step": state.get("step", 0) + 1,
    }
