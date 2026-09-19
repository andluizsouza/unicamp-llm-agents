"""LangGraph state for the multiagent architecture."""

from __future__ import annotations

from typing import Annotated, Any

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from recfair.schemas.intent import ParsedIntent
from recfair.schemas.routing import AgentResult, RoutingDecision


class MultiAgentState(TypedDict, total=False):
    """Shared state for the supervisor graph."""

    query: str
    query_sanitized: str
    thread_id: str
    messages: Annotated[list[Any], add_messages]
    session_intent: dict[str, Any]
    parsed_intent: ParsedIntent
    scoring_trace: list[dict[str, Any]]
    ranked_skus: list[str]
    routing: RoutingDecision
    last_result: AgentResult
    faq_evidence: list[dict[str, Any]]
    faq_status: str
    output: Any
    agent_traces: list[dict[str, Any]]
    agents_route: list[str]
    step: int
    halt_reason: str | None
    tool_calls: int
    chamadas_llm: int
    tokens_entrada: int
    tokens_saida: int
    errors: list[str]
