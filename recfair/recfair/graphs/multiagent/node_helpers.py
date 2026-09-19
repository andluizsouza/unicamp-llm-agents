"""Shared helpers for multiagent LangGraph nodes."""

from __future__ import annotations

from recfair.graphs.multiagent.state import MultiAgentState


def agents_route(state: MultiAgentState, agent_id: str) -> list[str]:
    """Build the cumulative agent route including the current step."""
    prior = [row["agent_id"] for row in (state.get("agent_traces") or [])]
    return prior + [agent_id]
