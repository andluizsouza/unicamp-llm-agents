"""LangGraph state for the workflow architecture."""

from __future__ import annotations

from typing import Annotated, Any

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from recfair.scoring.intent import ParsedIntent


class WorkflowState(TypedDict, total=False):
    """Shared state for the workflow graph."""

    query: str
    thread_id: str
    messages: Annotated[list[Any], add_messages]
    session_intent: dict[str, Any]
    parsed_intent: ParsedIntent
    scoring_trace: list[dict[str, Any]]
    ranked_skus: list[str]
    output: Any
    step: int
    halt_reason: str | None
    tool_calls: int
    chamadas_llm: int
    tokens_entrada: int
    tokens_saida: int
