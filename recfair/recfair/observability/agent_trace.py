"""Per-agent observability for the multiagent architecture."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from recfair.observability.tokens import estimate_llm_cost_usd


class AgentTrace(BaseModel):
    """One node/agent step in a multiagent invocation."""

    agent_id: str
    routing_reason: str | None = None
    plan: list[str] = Field(default_factory=list)
    replanned: bool = False
    chamadas_llm: int = 0
    tool_calls: int = 0
    latencia_s: float = 0.0
    tokens_entrada: int = 0
    tokens_saida: int = 0

    def cost_usd(self) -> float:
        """Estimated LLM cost for this step."""
        return estimate_llm_cost_usd(self.tokens_entrada, self.tokens_saida)

    def to_dict(self) -> dict[str, Any]:
        """Serialize including estimated ``custo_usd`` for CLI and manifests."""
        payload = self.model_dump()
        payload["custo_usd"] = round(self.cost_usd(), 6)
        return payload


def _serialize_traces(rows: list[Any]) -> list[dict[str, Any]]:
    """Normalize raw state traces (dicts or models) and attach ``custo_usd``."""
    steps: list[AgentTrace] = []
    for row in rows:
        if isinstance(row, AgentTrace):
            steps.append(row)
            continue
        if isinstance(row, dict):
            payload = {key: value for key, value in row.items() if key != "custo_usd"}
            steps.append(AgentTrace.model_validate(payload))
    return [step.to_dict() for step in steps]


def traces_to_dicts(rows: list[Any]) -> list[dict[str, Any]]:
    """Normalize raw state traces (dicts or models) and attach ``custo_usd``."""
    return _serialize_traces(rows)


def append_trace(state: dict[str, Any], trace: AgentTrace) -> list[dict[str, Any]]:
    """Concatenate one step onto this turn's traces (last-value channel)."""
    return list(state.get("agent_traces") or []) + [trace.to_dict()]
