"""Synthetic inventory snapshot aligned with ``catalog.TODAY``."""

from __future__ import annotations

from typing import Any

from recfair.data.catalog import CATALOG, UNITS_REST_DEFAULT

INVENTORY_SNAPSHOT_DATE = "2026-09-01"
INVENTORY_FIELDS = ("date", "cod_sku", "units_available", "is_launch", "is_promo")

# Hair SKU outside the 7-day Top-5 (T35 / G_stock out-of-stock trap).
_OUT_OF_STOCK = frozenset({"E4N8J1"})
# Low-seller perfumaria feminina launch flag (T24 / T37); not in category Top-5.
_LAUNCH = frozenset({"G7Q2D4"})
# Moderate-sales hair SKU promo flag (T25 / T37); not in category Top-5.
_PROMO = frozenset({"3G7P2W"})


def inventory_records() -> list[dict[str, Any]]:
    """Return one inventory row per catalog SKU for ``INVENTORY_SNAPSHOT_DATE``."""
    rows: list[dict[str, Any]] = []
    for row in CATALOG:
        sku = row["cod_sku"]
        rows.append(
            {
                "date": INVENTORY_SNAPSHOT_DATE,
                "cod_sku": sku,
                "units_available": 0 if sku in _OUT_OF_STOCK else UNITS_REST_DEFAULT,
                "is_launch": 1 if sku in _LAUNCH else 0,
                "is_promo": 1 if sku in _PROMO else 0,
            }
        )
    return rows


def inventory_by_sku() -> dict[str, dict[str, Any]]:
    """Map SKU code to the inventory snapshot row."""
    return {row["cod_sku"]: row for row in inventory_records()}
