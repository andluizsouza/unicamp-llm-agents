"""E3 multiagent: supervisor + recommendation + FAQ, security/handoff nodes."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from recfair.graphs.multiagent.nodes.faq import faq_node, route_after_faq
from recfair.graphs.multiagent.nodes.handoff import handoff_node
from recfair.graphs.multiagent.nodes.recommend import recommendation_node, route_after_recommend
from recfair.graphs.multiagent.nodes.security import security_node
from recfair.graphs.multiagent.nodes.supervisor import route_from_supervisor, supervisor_node
from recfair.graphs.multiagent.state import MultiAgentState
from recfair.observability.agent_trace import traces_to_dicts
from recfair.prompts.multiagent_v3 import PROMPT_VERSION
from recfair.schemas.output import RecFairOutput

_ARCHITECTURE_ID = "multiagent"
_ARCHITECTURE_DATE = "2026-09-19"
_RECURSION_LIMIT = 16

_GRAPH: Any = None
_CHECKPOINTER = MemorySaver()


@dataclass
class CaseMetrics:
    """Per-invocation instrumentation, including per-agent traces."""

    latencia_s: float
    tokens_entrada: int | None
    tokens_saida: int | None
    chamadas_llm: int
    tool_calls: int
    scoring_trace: list[dict[str, Any]] = field(default_factory=list)
    agent_traces: list[dict[str, Any]] = field(default_factory=list)
    agents_route: list[str] = field(default_factory=list)
    routing_plan: list[str] = field(default_factory=list)
    replanned: bool = False
    erro: str | None = None


def architecture_id() -> str:
    return _ARCHITECTURE_ID


def architecture_date() -> str:
    return _ARCHITECTURE_DATE


def prompt_version() -> str:
    return PROMPT_VERSION


def build_graph() -> Any:
    """Compile the multiagent LangGraph."""
    global _GRAPH
    if _GRAPH is not None:
        return _GRAPH
    graph = StateGraph(MultiAgentState)
    graph.add_node("security", security_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("recommendation", recommendation_node)
    graph.add_node("faq", faq_node)
    graph.add_node("handoff", handoff_node)
    graph.set_entry_point("security")
    graph.add_edge("security", "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "recommendation": "recommendation",
            "faq": "faq",
            "handoff": "handoff",
        },
    )
    graph.add_conditional_edges(
        "faq",
        route_after_faq,
        {"handoff": "handoff", "end": END},
    )
    graph.add_conditional_edges(
        "recommendation",
        route_after_recommend,
        {"handoff": "handoff", "end": END},
    )
    graph.add_edge("handoff", END)
    _GRAPH = graph.compile(checkpointer=_CHECKPOINTER)
    return _GRAPH


def run(query: str, thread_id: str | None = None) -> tuple[RecFairOutput, CaseMetrics]:
    """Execute the multiagent graph for one user query."""
    compiled = build_graph()
    tid = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": tid}, "recursion_limit": _RECURSION_LIMIT}
    initial: MultiAgentState = {
        "query": query,
        "thread_id": tid,
        "chamadas_llm": 0,
        "tokens_entrada": 0,
        "tokens_saida": 0,
        "tool_calls": 0,
        "step": 0,
        "agent_traces": [],
        "errors": [],
        "agents_route": [],
        "scoring_trace": [],
    }
    start = time.perf_counter()
    try:
        final = compiled.invoke(initial, config=config)
        latency = time.perf_counter() - start
        output = final.get("output")
        if output is None:
            output = RecFairOutput(
                status="abstention",
                reason=None,
                halt_reason="schema_invalid",
                agents_route=list(final.get("agents_route") or []),
            )
        tokens_in = final.get("tokens_entrada", 0)
        tokens_out = final.get("tokens_saida", 0)
        traces = traces_to_dicts(list(final.get("agent_traces") or []))
        routing = final.get("routing")
        return output, CaseMetrics(
            latencia_s=round(latency, 2),
            tokens_entrada=tokens_in if tokens_in else None,
            tokens_saida=tokens_out if tokens_out else None,
            chamadas_llm=final.get("chamadas_llm", 0),
            tool_calls=final.get("tool_calls", 0),
            scoring_trace=final.get("scoring_trace") or [],
            agent_traces=traces,
            agents_route=list(output.agents_route or final.get("agents_route") or []),
            routing_plan=list(routing.plan) if routing else [],
            replanned=bool(routing.replanned) if routing else False,
        )
    except Exception as exc:
        latency = time.perf_counter() - start
        halt = "recursion_limit" if "recursion" in str(exc).lower() else "schema_invalid"
        fallback = RecFairOutput(
            status="abstention",
            reason=None,
            halt_reason=halt,
            agents_route=["security", "supervisor"],
        )
        return fallback, CaseMetrics(
            latencia_s=round(latency, 2),
            tokens_entrada=None,
            tokens_saida=None,
            chamadas_llm=1,
            tool_calls=0,
            erro=f"{type(exc).__name__}: {exc}",
            agents_route=fallback.agents_route,
        )


def reset_checkpoint(thread_id: str) -> None:
    """Clear in-memory checkpoint for a thread (CLI /reset)."""
    build_graph().checkpointer.delete_thread(thread_id)
