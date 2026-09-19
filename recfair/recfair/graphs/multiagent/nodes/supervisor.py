"""Supervisor agent — structured routing over the skill index."""

from __future__ import annotations

import time
from typing import Any

from recfair.graphs.multiagent.llm import make_structured_llm, unpack_structured
from recfair.graphs.multiagent.skills import skills_index
from recfair.graphs.multiagent.state import MultiAgentState
from recfair.observability.agent_trace import AgentTrace, append_trace
from recfair.prompts.multiagent_v3 import build_supervisor_prompt
from recfair.schemas.routing import RoutingDecision

_STRUCTURED: Any = None
_LOW_CONFIDENCE = 0.45


def _structured() -> Any:
    global _STRUCTURED
    if _STRUCTURED is None:
        _STRUCTURED = make_structured_llm(RoutingDecision)
    return _STRUCTURED


def _coerce(decision: RoutingDecision) -> RoutingDecision:
    """Normalize domain/skill/plan; low confidence becomes handoff."""
    if decision.confidence < _LOW_CONFIDENCE:
        return RoutingDecision(
            domain="handoff",
            skill=None,
            plan=["handoff"],
            routing_reason=decision.routing_reason + " (confidence baixa → handoff)",
            confidence=decision.confidence,
        )
    if decision.domain == "handoff":
        return decision.model_copy(update={"skill": None, "plan": ["handoff"]})
    if decision.domain == "recommendation":
        return decision.model_copy(update={"skill": "skill_recommend", "plan": ["skill_recommend"]})
    return decision.model_copy(update={"skill": "skill_faq", "plan": ["skill_faq"]})


def supervisor_node(state: MultiAgentState) -> dict[str, Any]:
    """Classify domain and emit a one-step ``RoutingDecision``."""
    start = time.perf_counter()
    query = state.get("query_sanitized") or state["query"]
    packed = _structured().invoke(build_supervisor_prompt(query, skills_index()))
    parsed, tokens_in, tokens_out = unpack_structured(packed)
    decision = _coerce(parsed)
    latency = round(time.perf_counter() - start, 4)
    trace = AgentTrace(
        agent_id="supervisor",
        routing_reason=decision.routing_reason,
        plan=list(decision.plan),
        replanned=decision.replanned,
        chamadas_llm=1,
        latencia_s=latency,
        tokens_entrada=tokens_in or 0,
        tokens_saida=tokens_out or 0,
    )
    return {
        "routing": decision,
        "agent_traces": append_trace(state, trace),
        "chamadas_llm": state.get("chamadas_llm", 0) + 1,
        "tokens_entrada": state.get("tokens_entrada", 0) + (tokens_in or 0),
        "tokens_saida": state.get("tokens_saida", 0) + (tokens_out or 0),
        "step": state.get("step", 0) + 1,
    }


def route_from_supervisor(state: MultiAgentState) -> str:
    """Conditional edge after the supervisor."""
    routing = state.get("routing")
    if routing is None:
        return "handoff"
    return routing.domain
