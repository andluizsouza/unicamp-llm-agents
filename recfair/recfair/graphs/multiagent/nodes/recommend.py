"""Recommendation specialist — E2 pipeline plus semantic claims."""

from __future__ import annotations

import logging
import time
from typing import Any

from recfair.graphs.multiagent.skills import load_skill
from recfair.graphs.multiagent.state import MultiAgentState
from recfair.graphs.workflow.nodes.intent import parse_intent_node
from recfair.graphs.workflow.nodes.scoring import abstain_node, synthesize_node
from recfair.observability.agent_trace import AgentTrace, append_trace
from recfair.schemas.output import RecFairOutput
from recfair.schemas.routing import AgentMetrics, AgentResult
from recfair.tools.claims_semantic import match_claims_semantic
from recfair.tools.scoring.engine import score_recommendation

_LOG = logging.getLogger(__name__)


def _with_route(output: RecFairOutput, route: list[str]) -> RecFairOutput:
    return output.model_copy(update={"agents_route": route})


def _route(state: MultiAgentState) -> list[str]:
    prior = [row["agent_id"] for row in (state.get("agent_traces") or [])]
    return prior + ["recommendation"]


def _error_update(
    state: MultiAgentState,
    *,
    latency: float,
    extra_tools: int,
    extra_llm: int,
    error: str,
    skill_index: str,
) -> dict[str, Any]:
    """Structured tool/LLM failure: handoff edge, never a silent swallow."""
    routing = state.get("routing")
    tokens_in = int(state.get("tokens_entrada") or 0)
    tokens_out = int(state.get("tokens_saida") or 0)
    llm_calls = int(state.get("chamadas_llm") or 0) + extra_llm
    trace = AgentTrace(
        agent_id="recommendation",
        routing_reason=(routing.routing_reason if routing else None) or error,
        plan=list(routing.plan) if routing else ["skill_recommend"],
        replanned=False,
        chamadas_llm=max(extra_llm, 1),
        tool_calls=extra_tools,
        latencia_s=latency,
        tokens_entrada=tokens_in,
        tokens_saida=tokens_out,
    )
    last_result = AgentResult(
        agent_id="recommendation",
        status="error",
        payload={"skill": skill_index, "error": error},
        metrics=AgentMetrics(
            latencia_s=latency,
            chamadas_llm=max(extra_llm, 1),
            tool_calls=extra_tools,
            tokens_entrada=tokens_in,
            tokens_saida=tokens_out,
        ),
    )
    _LOG.warning("recommendation specialist failed: %s", error)
    return {
        "last_result": last_result,
        "agent_traces": append_trace(state, trace),
        "chamadas_llm": llm_calls,
        "tokens_entrada": tokens_in,
        "tokens_saida": tokens_out,
        "tool_calls": state.get("tool_calls", 0) + extra_tools,
        "step": state.get("step", 0) + 1,
        "errors": [error],
    }


def recommendation_node(state: MultiAgentState) -> dict[str, Any]:
    """Parse intent, score with semantic claims, synthesize RecFairOutput."""
    start = time.perf_counter()
    skill = load_skill("skill_recommend")
    query = state.get("query_sanitized") or state["query"]
    extra_tools = 0
    scoring_trace: list[dict[str, Any]] = []
    ranked: list[str] = []
    intent_update: dict[str, Any] | None = None

    try:
        intent_update = parse_intent_node({**state, "query": query})
    except Exception as exc:
        latency = round(time.perf_counter() - start, 4)
        return _error_update(
            state,
            latency=latency,
            extra_tools=0,
            extra_llm=1,
            error=f"{type(exc).__name__}: {exc}",
            skill_index=str(skill["index"]),
        )

    merged: MultiAgentState = {**state, **intent_update}
    parsed = intent_update["parsed_intent"]
    try:
        if parsed.abstain:
            out_update = abstain_node(merged)
        else:
            result = score_recommendation(parsed, claim_matcher=match_claims_semantic)
            extra_tools = result.tool_calls + 1
            scoring_trace = result.trace.to_dicts()
            ranked = result.skus
            merged = {
                **merged,
                "ranked_skus": ranked,
                "scoring_trace": scoring_trace,
                "tool_calls": state.get("tool_calls", 0) + extra_tools,
            }
            out_update = synthesize_node(merged)
    except Exception as exc:
        latency = round(time.perf_counter() - start, 4)
        return _error_update(
            merged,
            latency=latency,
            extra_tools=extra_tools,
            extra_llm=0,
            error=f"{type(exc).__name__}: {exc}",
            skill_index=str(skill["index"]),
        )

    latency = round(time.perf_counter() - start, 4)
    route = _route(state)
    output = _with_route(out_update["output"], route)
    tokens_in = intent_update.get("tokens_entrada", 0) - state.get("tokens_entrada", 0)
    tokens_out = intent_update.get("tokens_saida", 0) - state.get("tokens_saida", 0)
    routing = state.get("routing")
    trace = AgentTrace(
        agent_id="recommendation",
        routing_reason=routing.routing_reason if routing else skill["index"],
        plan=list(routing.plan) if routing else ["skill_recommend"],
        replanned=bool(routing.replanned) if routing else False,
        chamadas_llm=1,
        tool_calls=extra_tools,
        latencia_s=latency,
        tokens_entrada=max(tokens_in, 0),
        tokens_saida=max(tokens_out, 0),
    )
    last_result = AgentResult(
        agent_id="recommendation",
        status="ok",
        payload={
            "skill": skill["index"],
            "instruction": skill["instruction"],
            "intent": parsed.model_dump(),
            "ranked_skus": ranked,
        },
        metrics=AgentMetrics(
            latencia_s=latency,
            chamadas_llm=1,
            tool_calls=extra_tools,
            tokens_entrada=max(tokens_in, 0),
            tokens_saida=max(tokens_out, 0),
        ),
    )
    return {
        "parsed_intent": parsed,
        "session_intent": intent_update.get("session_intent"),
        "ranked_skus": ranked,
        "scoring_trace": scoring_trace,
        "output": output,
        "last_result": last_result,
        "agents_route": route,
        "agent_traces": append_trace(state, trace),
        "chamadas_llm": intent_update.get("chamadas_llm", state.get("chamadas_llm", 0) + 1),
        "tokens_entrada": intent_update.get("tokens_entrada", 0),
        "tokens_saida": intent_update.get("tokens_saida", 0),
        "tool_calls": state.get("tool_calls", 0) + extra_tools,
        "step": state.get("step", 0) + 2,
    }


def route_after_recommend(state: MultiAgentState) -> str:
    """Send tool/LLM errors to handoff; otherwise end."""
    result = state.get("last_result")
    if result is not None and result.status == "error":
        return "handoff"
    return "end"
