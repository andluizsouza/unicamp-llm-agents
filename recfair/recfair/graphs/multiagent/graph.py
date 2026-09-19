"""LangGraph compilation for the multiagent architecture."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from recfair.graphs.multiagent.nodes.faq import faq_node, route_after_faq
from recfair.graphs.multiagent.nodes.handoff import handoff_node
from recfair.graphs.multiagent.nodes.out_of_context import out_of_context_node
from recfair.graphs.multiagent.nodes.recommend import recommendation_node, route_after_recommend
from recfair.graphs.multiagent.nodes.security import security_node
from recfair.graphs.multiagent.nodes.supervisor import route_from_supervisor, supervisor_node
from recfair.graphs.multiagent.state import MultiAgentState

_RECURSION_LIMIT = 16

_GRAPH: Any = None
_CHECKPOINTER = MemorySaver()


def recursion_limit() -> int:
    """Max LangGraph steps for one user turn."""
    return _RECURSION_LIMIT


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
    graph.add_node("out_of_context", out_of_context_node)
    graph.set_entry_point("security")
    graph.add_edge("security", "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "recommendation": "recommendation",
            "faq": "faq",
            "handoff": "handoff",
            "out_of_context": "out_of_context",
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
    graph.add_edge("out_of_context", END)
    _GRAPH = graph.compile(checkpointer=_CHECKPOINTER)
    return _GRAPH
