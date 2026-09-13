"""E2 workflow: intent parsing + deterministic scoring pipeline."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from recfair.graphs.workflow.nodes.intent import parse_intent_node, route_after_intent
from recfair.graphs.workflow.nodes.scoring import abstain_node, scoring_node, synthesize_node
from recfair.graphs.workflow.state import WorkflowState
from recfair.prompts.workflow_v2 import PROMPT_VERSION
from recfair.schemas.output import RecFairOutput

_ARCHITECTURE_ID = "workflow"
_ARCHITECTURE_DATE = "2026-09-13"
_RECURSION_LIMIT = 12

_GRAPH: Any = None
_CHECKPOINTER = MemorySaver()


@dataclass
class CaseMetrics:
    """Per-invocation instrumentation."""

    latencia_s: float
    tokens_entrada: int | None
    tokens_saida: int | None
    chamadas_llm: int
    tool_calls: int
    scoring_trace: list[dict[str, Any]] = field(default_factory=list)
    erro: str | None = None


def architecture_id() -> str:
    return _ARCHITECTURE_ID


def architecture_date() -> str:
    return _ARCHITECTURE_DATE


def prompt_version() -> str:
    return PROMPT_VERSION


def build_graph() -> Any:
    """Compile the workflow LangGraph."""
    global _GRAPH
    if _GRAPH is not None:
        return _GRAPH
    graph = StateGraph(WorkflowState)
    graph.add_node("parse_intent", parse_intent_node)
    graph.add_node("score", scoring_node)
    graph.add_node("abstain", abstain_node)
    graph.add_node("synthesize", synthesize_node)
    graph.set_entry_point("parse_intent")
    graph.add_conditional_edges(
        "parse_intent",
        route_after_intent,
        {"abstain": "abstain", "score": "score"},
    )
    graph.add_edge("score", "synthesize")
    graph.add_edge("abstain", END)
    graph.add_edge("synthesize", END)
    _GRAPH = graph.compile(checkpointer=_CHECKPOINTER)
    return _GRAPH


def run(query: str, thread_id: str | None = None) -> tuple[RecFairOutput, CaseMetrics]:
    """Execute workflow for one user query."""
    compiled = build_graph()
    tid = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": tid}, "recursion_limit": _RECURSION_LIMIT}
    # Do not pass session_intent on invoke: LangGraph merges input with the
    # checkpoint and an empty dict wipes persisted session memory on turn 2+.
    initial: WorkflowState = {
        "query": query,
        "thread_id": tid,
        "chamadas_llm": 0,
        "tokens_entrada": 0,
        "tokens_saida": 0,
        "tool_calls": 0,
        "step": 0,
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
            )
        tokens_in = final.get("tokens_entrada", 0)
        tokens_out = final.get("tokens_saida", 0)
        metrics = CaseMetrics(
            latencia_s=round(latency, 2),
            tokens_entrada=tokens_in if tokens_in else None,
            tokens_saida=tokens_out if tokens_out else None,
            chamadas_llm=final.get("chamadas_llm", 1),
            tool_calls=final.get("tool_calls", 0),
            scoring_trace=final.get("scoring_trace") or [],
        )
        return output, metrics
    except Exception as exc:
        latency = time.perf_counter() - start
        fallback = RecFairOutput(
            status="abstention",
            reason=None,
            halt_reason="schema_invalid",
        )
        halt = "recursion_limit" if "recursion" in str(exc).lower() else "schema_invalid"
        if halt == "recursion_limit":
            fallback = RecFairOutput(
                status="abstention", reason=None, halt_reason="recursion_limit"
            )
        return fallback, CaseMetrics(
            latencia_s=round(latency, 2),
            tokens_entrada=None,
            tokens_saida=None,
            chamadas_llm=1,
            tool_calls=0,
            erro=f"{type(exc).__name__}: {exc}",
        )


def reset_checkpoint(thread_id: str) -> None:
    """Clear in-memory checkpoint for a thread (CLI /reset)."""
    build_graph().checkpointer.delete_thread(thread_id)
