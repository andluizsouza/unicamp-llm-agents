"""Stable data contracts between architectures, tools and eval."""

from recfair.schemas.intent import AbstainReason, ParsedIntent
from recfair.schemas.output import RecFairOutput, RecommendationItem
from recfair.schemas.routing import AgentMetrics, AgentResult, RoutingDecision

__all__ = [
    "AbstainReason",
    "AgentMetrics",
    "AgentResult",
    "ParsedIntent",
    "RecFairOutput",
    "RecommendationItem",
    "RoutingDecision",
]
