"""Gold labels derived from the scoring engine (E2 unified ruler)."""

from __future__ import annotations

from typing import Any

from eval.case_intent import intent_from_case
from recfair.data.catalog import catalog_by_sku, generate_sales
from recfair.tools.scoring.engine import score_recommendation

_SALES_ROWS = generate_sales()
_CATALOG = catalog_by_sku()


def sales_rows() -> list[dict[str, Any]]:
    """Cached daily sales rows."""
    return _SALES_ROWS


def catalog() -> dict[str, dict[str, Any]]:
    """Cached catalog by SKU."""
    return _CATALOG


def gold_for(case: dict[str, Any]) -> list[str]:
    """Expected SKU list for a golden case via the scoring engine."""
    intent = intent_from_case(case)
    if intent.abstain:
        return []
    result = score_recommendation(intent)
    return result.skus


def gold_for_price_cap(case: dict[str, Any], max_brl: float) -> list[str]:
    """Top-N with price cap — delegates to scoring engine."""
    from recfair.schemas.intent import ParsedIntent

    intent = ParsedIntent(
        category=case.get("category"),
        brand=case.get("brand"),
        max_price_brl=max_brl,
        require_diversity=bool(case.get("require_diversity")),
    )
    return score_recommendation(intent).skus
