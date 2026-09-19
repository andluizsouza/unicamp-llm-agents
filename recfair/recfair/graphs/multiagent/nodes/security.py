"""Deterministic security node — regex redact, zero LLM."""

from __future__ import annotations

import time
from typing import Any

from recfair.graphs.multiagent.state import MultiAgentState
from recfair.observability.agent_trace import AgentTrace, append_trace
from recfair.tools.guardrails import sanitize_query


def security_node(state: MultiAgentState) -> dict[str, Any]:
    """Sanitize the user query before any LLM sees it."""
    start = time.perf_counter()
    result = sanitize_query(state["query"])
    latency = round(time.perf_counter() - start, 4)
    flags = []
    if result.pii_types:
        flags.append("pii:" + ",".join(result.pii_types))
    if result.injection:
        flags.append("injection")
    if result.jailbreak:
        flags.append("jailbreak")
    reason = "; ".join(flags) if flags else "clean"
    trace = AgentTrace(
        agent_id="security",
        routing_reason=reason,
        latencia_s=latency,
    )
    return {
        "query_sanitized": result.sanitized,
        "agent_traces": append_trace(state, trace),
        "step": state.get("step", 0) + 1,
        "tool_calls": state.get("tool_calls", 0) + 1,
    }
