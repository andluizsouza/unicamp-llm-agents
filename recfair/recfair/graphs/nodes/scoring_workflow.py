"""Deterministic scoring nodes for the workflow graph."""

from __future__ import annotations

from typing import Any

from recfair.config import N_RECOMMEND
from recfair.data.catalog import catalog_by_sku, generate_sales, units_in_window
from recfair.graphs.state import WorkflowState
from recfair.schemas.output import RecFairOutput, RecommendationItem
from recfair.scoring.engine import score_recommendation


def scoring_node(state: WorkflowState) -> dict[str, Any]:
    """Run the scoring engine on the parsed intent."""
    intent = state["parsed_intent"]
    result = score_recommendation(intent)
    return {
        "ranked_skus": result.skus,
        "scoring_trace": result.trace.to_dicts(),
        "tool_calls": state.get("tool_calls", 0) + result.tool_calls,
        "step": state.get("step", 0) + 1,
    }


def abstain_node(state: WorkflowState) -> dict[str, Any]:
    """Format abstention output."""
    intent = state["parsed_intent"]
    output = RecFairOutput(
        status="abstention",
        reason=intent.abstain_reason,
        halt_reason="abstained",
    )
    return {"output": output, "step": state.get("step", 0) + 1}


def synthesize_node(state: WorkflowState) -> dict[str, Any]:
    """Build RecFairOutput from ranked SKUs."""
    catalog = catalog_by_sku()
    units_7d = units_in_window(generate_sales())

    skus = state.get("ranked_skus") or []
    if not skus:
        output = RecFairOutput(
            status="abstention",
            reason="missing_category",
            halt_reason="abstained",
        )
        return {"output": output, "step": state.get("step", 0) + 1}

    items: list[RecommendationItem] = []
    for sku in skus[:N_RECOMMEND]:
        meta = catalog[sku]
        items.append(
            RecommendationItem(
                sku=sku,
                name=meta["name_sku"],
                brand=meta["brand"],
                category=meta["category"],
                units_7d=units_7d.get(sku, 0),
                price_brl=float(meta["base_price"]),
            )
        )
    output = RecFairOutput(
        status="recommendation",
        items=items,
        halt_reason="completed",
    )
    return {"output": output, "step": state.get("step", 0) + 1}
