"""Workflow checkpoint memory regression tests (no LLM)."""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from recfair.graphs.workflow import reset_checkpoint


class _State(TypedDict, total=False):
    query: str
    session_intent: dict
    chamadas_llm: int


def _remember(state: _State) -> dict:
    prior = state.get("session_intent") or {}
    category = prior.get("category", "")
    if state["query"] == "turn1":
        category = "cabelos"
    return {
        "session_intent": {**prior, "category": category},
        "chamadas_llm": state.get("chamadas_llm", 0) + 1,
    }


def test_invoke_empty_session_intent_wipes_checkpoint() -> None:
    """Mirrors the pre-fix bug: passing session_intent={} on turn 2 clears memory."""
    graph = StateGraph(_State)
    graph.add_node("remember", _remember)
    graph.set_entry_point("remember")
    graph.add_edge("remember", END)
    compiled = graph.compile(checkpointer=MemorySaver())
    tid = "memory-regression"
    reset_checkpoint(tid)
    cfg = {"configurable": {"thread_id": tid}}

    compiled.invoke(
        {"query": "turn1", "session_intent": {}, "chamadas_llm": 0},
        config=cfg,
    )
    wiped = compiled.invoke(
        {"query": "turn2", "session_intent": {}, "chamadas_llm": 0},
        config=cfg,
    )
    assert wiped["session_intent"].get("category") == ""

    reset_checkpoint(tid)
    compiled.invoke({"query": "turn1", "chamadas_llm": 0}, config=cfg)
    kept = compiled.invoke({"query": "turn2", "chamadas_llm": 0}, config=cfg)
    assert kept["session_intent"].get("category") == "cabelos"
