"""Contracts between the multiagent supervisor and specialist agents."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Domain = Literal["recommendation", "faq", "handoff"]
SkillName = Literal["skill_recommend", "skill_faq"]
AgentStatus = Literal["ok", "no_evidence", "error"]


class AgentMetrics(BaseModel):
    """Per-agent instrumentation attached to ``AgentResult``."""

    latencia_s: float = 0.0
    chamadas_llm: int = 0
    tool_calls: int = 0
    tokens_entrada: int = 0
    tokens_saida: int = 0


class RoutingDecision(BaseModel):
    """Supervisor plan: one skill, or handoff with skill omitted."""

    domain: Domain
    skill: SkillName | None = None
    plan: list[str] = Field(default_factory=list)
    routing_reason: str
    confidence: float = 1.0
    replanned: bool = False


class AgentResult(BaseModel):
    """Structured specialist output consumed by downstream nodes."""

    agent_id: str
    status: AgentStatus
    payload: dict[str, Any] = Field(default_factory=dict)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    metrics: AgentMetrics = Field(default_factory=AgentMetrics)
