"""Deterministic scoring nodes for the workflow graph."""

from __future__ import annotations

from typing import Any

from recfair.config import N_RECOMMEND
from recfair.data.catalog import catalog_by_sku, generate_sales, units_in_window
from recfair.data.inventory import inventory_by_sku
from recfair.graphs.workflow.state import WorkflowState
from recfair.schemas.intent import ParsedIntent
from recfair.schemas.output import RecFairOutput, RecommendationItem
from recfair.tools.scoring.engine import score_recommendation

_ABSTAIN_TEXT = {
    "missing_category": "Abstenção: a categoria não pôde ser determinada.",
    "unknown_category": "Abstenção: a categoria pedida não existe no catálogo.",
    "unknown_brand": "Abstenção: a marca pedida não existe no catálogo.",
}


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


def _inventory_flags(row: dict[str, Any] | None) -> tuple[bool | None, bool | None, bool | None]:
    """Map one inventory row to stock, launch, and promo flags.

    Returns:
        ``(in_stock, is_launch, is_promo)``. Each value is ``None`` only when
        the snapshot row itself is missing.
    """
    if row is None:
        return None, None, None
    return (
        int(row["units_available"]) > 0,
        bool(int(row["is_launch"])),
        bool(int(row["is_promo"])),
    )


def _bonus_label(entry: dict[str, Any]) -> str:
    """Stable bonus name that does not copy user text from the trace."""
    step = str(entry.get("step") or "bonus")
    reason = str(entry.get("reason") or "")
    if step == "add_promo_launch" and reason in {"is_launch=true", "is_promo=true"}:
        return reason.removesuffix("=true")
    if step == "score_claims":
        return "claims"
    if step == "score_brand_diversity":
        return "diversidade_marca"
    return step


def _explanation(
    sku: str,
    trace: list[dict[str, Any]],
    *,
    units_7d: int,
) -> str:
    """Ranking rationale for one SKU, taken from the scoring trace."""
    points = 0
    rank: str | None = None
    bonuses: list[str] = []
    for entry in trace:
        if entry.get("sku") != sku:
            continue
        action = entry.get("action")
        if action == "bonus":
            delta = int(entry.get("points_delta") or 0)
            bonuses.append(f"{_bonus_label(entry)}+{delta}")
        elif action == "ranked":
            points = int(entry.get("points_total") or 0)
            head = str(entry.get("reason") or "").split(",", 1)[0].strip()
            if head.startswith("rank="):
                token = head.removeprefix("rank=")
                if token.isdigit():
                    rank = token
    parts = [f"pontos={points}", f"vendas_7d={units_7d}"]
    if rank is not None:
        parts.append(f"rank={rank}")
    if bonuses:
        parts.append("bonus=" + ",".join(bonuses))
    return "; ".join(parts)


def _recommendation_text(
    intent: ParsedIntent | None,
    *,
    categories: set[str],
    brands: set[str],
    n: int,
) -> str:
    """Factual vitrine summary. Omits raw query text and unknown labels."""
    bits = [f"Top-{n}"]
    if intent is not None and intent.category in categories:
        bits.append(f"em {intent.category}")
    if intent is not None and intent.brand and intent.brand in brands:
        bits.append(f"marca {intent.brand}")
    if intent is not None and intent.max_price_brl is not None:
        bits.append(f"preço até {intent.max_price_brl:g}")
    bits.append("ordenado por pontos, vendas em 7 dias e SKU")
    return " ".join(bits) + "."


def abstain_node(state: WorkflowState) -> dict[str, Any]:
    """Format abstention output."""
    intent = state["parsed_intent"]
    reason = intent.abstain_reason
    output = RecFairOutput(
        status="abstention",
        reason=reason,
        halt_reason="abstained",
        answer_text=_ABSTAIN_TEXT.get(reason or "", _ABSTAIN_TEXT["missing_category"]),
    )
    return {"output": output, "step": state.get("step", 0) + 1}


def synthesize_node(state: WorkflowState) -> dict[str, Any]:
    """Build RecFairOutput from ranked SKUs, inventory flags, and score trace."""
    catalog = catalog_by_sku()
    inventory = inventory_by_sku()
    units_7d = units_in_window(generate_sales())
    trace = list(state.get("scoring_trace") or [])
    intent = state.get("parsed_intent")

    skus = state.get("ranked_skus") or []
    if not skus:
        output = RecFairOutput(
            status="abstention",
            reason="missing_category",
            halt_reason="abstained",
            answer_text=_ABSTAIN_TEXT["missing_category"],
        )
        return {"output": output, "step": state.get("step", 0) + 1}

    brands = {row["brand"] for row in catalog.values()}
    categories = {row["category"] for row in catalog.values()}
    items: list[RecommendationItem] = []
    for sku in skus[:N_RECOMMEND]:
        meta = catalog[sku]
        sold = units_7d.get(sku, 0)
        in_stock, is_launch, is_promo = _inventory_flags(inventory.get(sku))
        items.append(
            RecommendationItem(
                sku=sku,
                name=meta["name_sku"],
                brand=meta["brand"],
                category=meta["category"],
                units_7d=sold,
                price_brl=float(meta["base_price"]),
                in_stock=in_stock,
                is_launch=is_launch,
                is_promo=is_promo,
                explanation=_explanation(sku, trace, units_7d=sold),
            )
        )
    output = RecFairOutput(
        status="recommendation",
        items=items,
        halt_reason="completed",
        answer_text=_recommendation_text(
            intent,
            categories=categories,
            brands=brands,
            n=len(items),
        ),
    )
    return {"output": output, "step": state.get("step", 0) + 1}
