"""Pandas gold labels for deterministic verification."""

from __future__ import annotations

from typing import Any

from recfair.config import N_RECOMMEND
from recfair.data.catalog import (
    catalog_by_sku,
    generate_sales,
    gold_top_n,
    gold_top_n_diverse,
    units_in_window,
)

_SALES_ROWS = generate_sales()
_CATALOG = catalog_by_sku()


def sales_rows() -> list[dict[str, Any]]:
    """Cached daily sales rows."""
    return _SALES_ROWS


def catalog() -> dict[str, dict[str, Any]]:
    """Cached catalog by SKU."""
    return _CATALOG


def gold_for(case: dict[str, Any]) -> list[str]:
    """Expected SKU list for a golden case."""
    if case.get("category") is None:
        return []
    use_diverse = bool(case.get("require_diversity")) and case.get("brand") is None
    if use_diverse:
        rows = gold_top_n_diverse(
            _SALES_ROWS,
            category=case["category"],
            n=N_RECOMMEND,
        )
    else:
        rows = gold_top_n(
            _SALES_ROWS,
            category=case["category"],
            brand=case.get("brand"),
            n=N_RECOMMEND,
        )
    return [r["cod_sku"] for r in rows]


def gold_for_price_cap(case: dict[str, Any], max_brl: float) -> list[str]:
    """Top-N in category/brand with catalog base_price <= max_brl."""
    totals = units_in_window(_SALES_ROWS)
    candidates: list[tuple[int, str]] = []
    for sku, meta in _CATALOG.items():
        if meta["category"] != case["category"]:
            continue
        if case.get("brand") and meta["brand"] != case["brand"]:
            continue
        if meta["base_price"] > max_brl:
            continue
        candidates.append((totals[sku], sku))
    candidates.sort(key=lambda row: (-row[0], row[1]))
    return [sku for _, sku in candidates[:N_RECOMMEND]]
