"""Deterministic scoring pipeline — single source of truth for gold labels."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from recfair.config import N_RECOMMEND
from recfair.data.catalog import (
    catalog_by_sku,
    generate_sales,
    units_in_window,
)
from recfair.data.claims import claims_records
from recfair.data.inventory import INVENTORY_SNAPSHOT_DATE, inventory_by_sku
from recfair.schemas.intent import ParsedIntent
from recfair.tools.scoring.trace import ScoreTrace

_CATALOG = catalog_by_sku()
_SALES = generate_sales()
_UNITS_7D = units_in_window(_SALES)
_INVENTORY = inventory_by_sku()
_CLAIMS_BY_SKU: dict[str, list[dict[str, str]]] = {}
for row in claims_records():
    _CLAIMS_BY_SKU.setdefault(row["cod_sku"], []).append(row)


@dataclass
class ScoringResult:
    """Output of the scoring workflow."""

    skus: list[str]
    trace: ScoreTrace
    points: dict[str, int]
    units_7d: dict[str, int]
    tool_calls: int


def _claims_text(sku: str) -> str:
    parts = [row["claim_text"] for row in _CLAIMS_BY_SKU.get(sku, [])]
    return " ".join(parts).lower()


def _claim_match(sku: str, terms: list[str]) -> str | None:
    if not terms:
        return None
    blob = _claims_text(sku)
    for term in terms:
        if term.lower() in blob:
            return term
    return None


ClaimMatcher = Callable[[str, list[str]], str | None]


def score_recommendation(
    intent: ParsedIntent,
    *,
    claim_matcher: ClaimMatcher | None = None,
) -> ScoringResult:
    """Run the seven-step scoring pipeline and return Top-N SKUs.

    Args:
        intent: Parsed filters from NL or golden-case metadata.
        claim_matcher: Optional replacement for substring claim matching.
            Default keeps E2/gold behaviour (``_claim_match``). The multiagent
            path injects semantic matching without changing the workflow.
    """
    trace = ScoreTrace()
    tool_calls = 0

    if intent.abstain or intent.category is None:
        trace.log("filter_by_category_brand", "-", "skipped", "abstain or missing category")
        return ScoringResult([], trace, {}, {}, tool_calls)

    # Step 1: filter by category and optional brand
    tool_calls += 1
    pool: list[str] = []
    for sku, meta in _CATALOG.items():
        if meta["category"] != intent.category:
            continue
        if intent.brand and meta["brand"] != intent.brand:
            continue
        pool.append(sku)
        trace.log(
            "filter_by_category_brand",
            sku,
            "pool",
            f"category={intent.category}" + (f", brand={intent.brand}" if intent.brand else ""),
        )

    if not pool:
        return ScoringResult([], trace, {}, {}, tool_calls)

    points: dict[str, int] = {sku: 0 for sku in pool}
    units: dict[str, int] = {sku: _UNITS_7D.get(sku, 0) for sku in pool}

    # Step 2: exclude stock and price
    tool_calls += 1
    survivors: list[str] = []
    for sku in pool:
        inv = _INVENTORY.get(sku, {})
        price = float(_CATALOG[sku]["base_price"])
        if inv.get("units_available", 0) <= 0:
            trace.log(
                "exclude_stock_and_price",
                sku,
                "removed",
                f"units_available=0 on {INVENTORY_SNAPSHOT_DATE}",
            )
            continue
        if intent.max_price_brl is not None and price > intent.max_price_brl:
            trace.log(
                "exclude_stock_and_price",
                sku,
                "removed",
                f"base_price {price} > max {intent.max_price_brl}",
            )
            continue
        survivors.append(sku)
        if intent.max_price_brl is None:
            reason = "in stock"
        else:
            reason = f"in stock, price {price} <= {intent.max_price_brl}"
        trace.log("exclude_stock_and_price", sku, "pool", reason)

    if not survivors:
        if intent.max_price_brl is None:
            trace.log("exclude_stock_and_price", "-", "skipped", "no exclusions applied")
        return ScoringResult([], trace, points, units, tool_calls)

    pool = survivors
    points = {sku: points.get(sku, 0) for sku in pool}
    units = {sku: units[sku] for sku in pool}

    # Step 3: score claims (+2)
    tool_calls += 1
    matcher = claim_matcher or _claim_match
    if intent.claim_terms:
        for sku in pool:
            matched = matcher(sku, intent.claim_terms)
            if matched:
                points[sku] += 2
                trace.log(
                    "score_claims",
                    sku,
                    "bonus",
                    f"match claim '{matched}'",
                    points_delta=2,
                    points_total=points[sku],
                )
    else:
        trace.log("score_claims", "-", "skipped", "no claim terms")

    # Step 4: brand diversity (+1 for brand representative)
    tool_calls += 1
    if intent.require_diversity:
        best_per_brand: dict[str, str] = {}
        for sku in pool:
            brand = _CATALOG[sku]["brand"]
            current = best_per_brand.get(brand)
            if current is None or (units[sku], sku) > (units[current], current):
                best_per_brand[brand] = sku
        for sku in best_per_brand.values():
            points[sku] += 1
            trace.log(
                "score_brand_diversity",
                sku,
                "bonus",
                f"brand representative ({_CATALOG[sku]['brand']})",
                points_delta=1,
                points_total=points[sku],
            )
    else:
        trace.log("score_brand_diversity", "-", "skipped", "diversity not required")

    # Step 5: promo / launch (+1 each)
    tool_calls += 1
    for sku in pool:
        inv = _INVENTORY.get(sku, {})
        if inv.get("is_launch"):
            points[sku] += 1
            trace.log(
                "add_promo_launch",
                sku,
                "bonus",
                "is_launch=true",
                points_delta=1,
                points_total=points[sku],
            )
        if inv.get("is_promo"):
            points[sku] += 1
            trace.log(
                "add_promo_launch",
                sku,
                "bonus",
                "is_promo=true",
                points_delta=1,
                points_total=points[sku],
            )

    # Step 6: rank by points, units_7d, cod_sku
    tool_calls += 1
    ranked = sorted(pool, key=lambda sku: (-points[sku], -units[sku], sku))
    for rank, sku in enumerate(ranked, start=1):
        trace.log(
            "rank_by_sales_tiebreak",
            sku,
            "ranked",
            f"rank={rank}, points={points[sku]}, units_7d={units[sku]}",
            points_total=points[sku],
        )

    # Step 7: top N
    tool_calls += 1
    top = ranked[:N_RECOMMEND]
    for sku in top:
        trace.log("assemble_top5", sku, "pool", f"selected in top {N_RECOMMEND}")

    return ScoringResult(top, trace, points, units, tool_calls)
