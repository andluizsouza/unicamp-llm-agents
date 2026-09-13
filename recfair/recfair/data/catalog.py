"""Generate RecFair synthetic catalog and daily sales CSVs.

The same module writes SQLite tables for the E2 text-to-SQL tool. Product names
and base prices are inspired by public pages on boticario.com.br (Sep 2026).
SKUs are invented opaque 6-character codes (not sequential, not mnemonic).
``base_price`` is a tabulated list price, not the live price.
"""

from __future__ import annotations

import csv
import re
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Any

TODAY = date(2026, 9, 1)
SALES_START = date(2026, 8, 1)
SALES_END = date(2026, 8, 31)
WINDOW_START = date(2026, 8, 25)
WINDOW_END = date(2026, 8, 31)
CATALOG_FIELDS = ("cod_sku", "name_sku", "brand", "category", "base_price")
SALES_FIELDS = ("date", "cod_sku", "qt_sold")
UNITS_REST_DEFAULT = 48
SKU_PATTERN = re.compile(r"^[A-Z0-9]{6}$")

CATEGORY_PERFUME_M = "perfumaria_masculina"
CATEGORY_PERFUME_F = "perfumaria_feminina"
CATEGORY_BODY = "corpo_e_banho"
CATEGORY_HAIR = "cabelos"


def _default_data_dir() -> Path:
    """Directory for CSVs at app ``data/``."""
    from recfair.config import data_dir

    return data_dir()


DATA_DIR = _default_data_dir()

# Opaque 6-char SKUs (fixed, not sequential, not mnemonic). Same values in CSV and SQLite.
SKU_CLASH = "6D2W9K"
SKU_ANTICASPA = "H8Q3N1"
SKU_HAIR_ALT = "A8T3K5"

CATALOG: list[dict[str, Any]] = [
    # Perfumaria masculina — 5 Malbec so a popularity Top-5 can be 5× one brand (T05).
    {
        "cod_sku": "7K2N9A",
        "name_sku": "Malbec Desodorante Colônia 100ml",
        "brand": "Malbec",
        "category": CATEGORY_PERFUME_M,
        "base_price": 219.90,
    },
    {
        "cod_sku": "Q4H8L2",
        "name_sku": "Malbec Eau de Parfum 90ml",
        "brand": "Malbec",
        "category": CATEGORY_PERFUME_M,
        "base_price": 279.90,
    },
    {
        "cod_sku": "3R1B6M",
        "name_sku": "Malbec Signature Eau de Parfum 90ml",
        "brand": "Malbec",
        "category": CATEGORY_PERFUME_M,
        "base_price": 379.90,
    },
    {
        "cod_sku": "W9C5TD",
        "name_sku": "Malbec Gold Desodorante Colônia 100ml",
        "brand": "Malbec",
        "category": CATEGORY_PERFUME_M,
        "base_price": 259.90,
    },
    {
        "cod_sku": "5J8P2X",
        "name_sku": "Malbec Club Intenso Desodorante Colônia 100ml",
        "brand": "Malbec",
        "category": CATEGORY_PERFUME_M,
        "base_price": 249.90,
    },
    {
        "cod_sku": "2M7K4F",
        "name_sku": "Zaad Eau de Parfum 95ml",
        "brand": "Zaad",
        "category": CATEGORY_PERFUME_M,
        "base_price": 349.90,
    },
    {
        "cod_sku": "H3L9Q1",
        "name_sku": "Quasar Deep Blue Desodorante Colônia 100ml",
        "brand": "Quasar",
        "category": CATEGORY_PERFUME_M,
        "base_price": 189.90,
    },
    {
        "cod_sku": "8V4C6N",
        "name_sku": "Arbo Desodorante Colônia 100ml",
        "brand": "Arbo",
        "category": CATEGORY_PERFUME_M,
        "base_price": 189.90,
    },
    {
        "cod_sku": "P1T8R5",
        "name_sku": "Egeo Bomb Black Desodorante Colônia 90ml",
        "brand": "Egeo",
        "category": CATEGORY_PERFUME_M,
        "base_price": 164.90,
    },
    {
        "cod_sku": SKU_CLASH,
        "name_sku": "Clash Desodorante Colônia 100ml",
        "brand": "Clash",
        "category": CATEGORY_PERFUME_M,
        "base_price": 179.90,
    },
    # Perfumaria feminina
    {
        "cod_sku": "8K2F6Q",
        "name_sku": "Lily Eau de Parfum 75ml",
        "brand": "Lily",
        "category": CATEGORY_PERFUME_F,
        "base_price": 294.90,
    },
    {
        "cod_sku": "D1W5N9",
        "name_sku": "Lily Gardênia Eau de Parfum 75ml",
        "brand": "Lily",
        "category": CATEGORY_PERFUME_F,
        "base_price": 294.90,
    },
    {
        "cod_sku": "6P8H3A",
        "name_sku": "Floratta Red Desodorante Colônia 75ml",
        "brand": "Floratta",
        "category": CATEGORY_PERFUME_F,
        "base_price": 146.85,
    },
    {
        "cod_sku": "Y4C2L7",
        "name_sku": "Floratta Blue Desodorante Colônia 75ml",
        "brand": "Floratta",
        "category": CATEGORY_PERFUME_F,
        "base_price": 174.90,
    },
    {
        "cod_sku": "1M9T5B",
        "name_sku": "Her Code Eau de Parfum 50ml",
        "brand": "Her Code",
        "category": CATEGORY_PERFUME_F,
        "base_price": 254.90,
    },
    {
        "cod_sku": "5X3R8K",
        "name_sku": "Coffee Woman Seduction Desodorante Colônia 100ml",
        "brand": "Coffee",
        "category": CATEGORY_PERFUME_F,
        "base_price": 229.90,
    },
    {
        "cod_sku": "G7Q2D4",
        "name_sku": "Elysée Blanc Eau de Parfum 50ml",
        "brand": "Elysée",
        "category": CATEGORY_PERFUME_F,
        "base_price": 329.90,
    },
    {
        "cod_sku": "N6A1V8",
        "name_sku": "Glamour Secrets Black Desodorante Colônia 75ml",
        "brand": "Glamour",
        "category": CATEGORY_PERFUME_F,
        "base_price": 150.90,
    },
    {
        "cod_sku": "2C8L4P",
        "name_sku": "Egeo Dolce Desodorante Colônia 90ml",
        "brand": "Egeo",
        "category": CATEGORY_PERFUME_F,
        "base_price": 164.90,
    },
    {
        "cod_sku": "9H5W1T",
        "name_sku": "Botica 214 Peônia e Apricot Eau de Parfum 75ml",
        "brand": "Botica 214",
        "category": CATEGORY_PERFUME_F,
        "base_price": 249.90,
    },
    # Corpo e banho — 5 Cuide-se Bem so a popularity Top-5 can be 5× one brand (T04).
    {
        "cod_sku": "24A51X",
        "name_sku": "Loção Hidratante Cuide-se Bem Nuvem 400ml",
        "brand": "Cuide-se Bem",
        "category": CATEGORY_BODY,
        "base_price": 57.90,
    },
    {
        "cod_sku": "K8M2Q1",
        "name_sku": "Sabonete em Barra Cuide-se Bem Cereja 2x80g",
        "brand": "Cuide-se Bem",
        "category": CATEGORY_BODY,
        "base_price": 21.90,
    },
    {
        "cod_sku": "9P3W7C",
        "name_sku": "Loção Hidratante Cuide-se Bem Deleite 400ml",
        "brand": "Cuide-se Bem",
        "category": CATEGORY_BODY,
        "base_price": 57.90,
    },
    {
        "cod_sku": "B7F4L9",
        "name_sku": "Loção Cuide-se Bem Rosa e Algodão 400ml",
        "brand": "Cuide-se Bem",
        "category": CATEGORY_BODY,
        "base_price": 57.90,
    },
    {
        "cod_sku": "T2N8H4",
        "name_sku": "Loção Hidratante Cuide-se Bem Beijinho 400ml",
        "brand": "Cuide-se Bem",
        "category": CATEGORY_BODY,
        "base_price": 57.90,
    },
    {
        "cod_sku": "Z5C1R8",
        "name_sku": "Loção Firmadora Corporal Nativa SPA Quinoa 400ml",
        "brand": "Nativa SPA",
        "category": CATEGORY_BODY,
        "base_price": 89.90,
    },
    {
        "cod_sku": "4W6J2P",
        "name_sku": "Sabonete Líquido Nativa SPA Orquídea Noire 250ml",
        "brand": "Nativa SPA",
        "category": CATEGORY_BODY,
        "base_price": 54.90,
    },
    {
        "cod_sku": "M9D3K7",
        "name_sku": "Refil Sabonete Líquido Nativa SPA Orquídea Noire 200ml",
        "brand": "Nativa SPA",
        "category": CATEGORY_BODY,
        "base_price": 44.90,
    },
    {
        "cod_sku": "X1Q8V3",
        "name_sku": "Sabonete em Barra Malbec 2x80g",
        "brand": "Malbec",
        "category": CATEGORY_BODY,
        "base_price": 31.90,
    },
    {
        "cod_sku": "7H5A2E",
        "name_sku": "Loção Hidratante Lily 250ml",
        "brand": "Lily",
        "category": CATEGORY_BODY,
        "base_price": 99.90,
    },
    # Cabelos — 5 Match (T01 trap); anticaspa is not in the 7-day Top-5 (T11).
    {
        "cod_sku": "F3P9W2",
        "name_sku": "Shampoo Match Ciência das Curvas 300ml",
        "brand": "Match",
        "category": CATEGORY_HAIR,
        "base_price": 45.90,
    },
    {
        "cod_sku": "L6K1C8",
        "name_sku": "Shampoo Match Oleosidade Controlada 300ml",
        "brand": "Match",
        "category": CATEGORY_HAIR,
        "base_price": 47.90,
    },
    {
        "cod_sku": "2Y8N4T",
        "name_sku": "Shampoo Match Liso Prolongado 300ml",
        "brand": "Match",
        "category": CATEGORY_HAIR,
        "base_price": 47.90,
    },
    {
        "cod_sku": "R5B7Q3",
        "name_sku": "Shampoo Match Nutrição Regeneradora 300ml",
        "brand": "Match",
        "category": CATEGORY_HAIR,
        "base_price": 47.90,
    },
    {
        "cod_sku": "9C4M1H",
        "name_sku": "Condicionador Match Nutrição Regeneradora 280ml",
        "brand": "Match",
        "category": CATEGORY_HAIR,
        "base_price": 49.90,
    },
    {
        "cod_sku": SKU_ANTICASPA,
        "name_sku": "Shampoo Esfoliante Anticaspa Malbec 150ml",
        "brand": "Malbec",
        "category": CATEGORY_HAIR,
        "base_price": 59.90,
    },
    {
        "cod_sku": "V2L9D6",
        "name_sku": "Shampoo Antiqueda Malbec 250ml",
        "brand": "Malbec",
        "category": CATEGORY_HAIR,
        "base_price": 55.90,
    },
    {
        "cod_sku": SKU_HAIR_ALT,
        "name_sku": "Shampoo Cuide-se Bem Feira Cachos de Uva 270ml",
        "brand": "Cuide-se Bem",
        "category": CATEGORY_HAIR,
        "base_price": 25.90,
    },
    {
        "cod_sku": "3G7P2W",
        "name_sku": "Shampoo Cuide-se Bem Feira Vinagre de Framboesa 230ml",
        "brand": "Cuide-se Bem",
        "category": CATEGORY_HAIR,
        "base_price": 27.90,
    },
    {
        "cod_sku": "E4N8J1",
        "name_sku": "Shampoo Cuide-se Bem Feira Óleo de Coco 230ml",
        "brand": "Cuide-se Bem",
        "category": CATEGORY_HAIR,
        "base_price": 25.90,
    },
]

# Window 25–31/08. Top-5 by units is 5× Malbec / 5× Cuide-se Bem / 5× Match.
UNITS_7D: dict[str, int] = {
    "7K2N9A": 400,
    "Q4H8L2": 350,
    "3R1B6M": 300,
    "5J8P2X": 210,
    "W9C5TD": 210,
    "2M7K4F": 150,
    "8V4C6N": 140,
    "H3L9Q1": 140,
    "P1T8R5": 120,
    SKU_CLASH: 25,
    "8K2F6Q": 400,
    "D1W5N9": 300,
    "6P8H3A": 250,
    "1M9T5B": 160,
    "5X3R8K": 150,
    "2C8L4P": 140,
    "N6A1V8": 130,
    "9H5W1T": 120,
    "Y4C2L7": 80,
    "G7Q2D4": 70,
    "24A51X": 220,
    "K8M2Q1": 205,
    "9P3W7C": 190,
    "B7F4L9": 180,
    "T2N8H4": 170,
    "Z5C1R8": 140,
    "4W6J2P": 90,
    "X1Q8V3": 80,
    "7H5A2E": 70,
    "M9D3K7": 50,
    "F3P9W2": 280,
    "L6K1C8": 210,
    "2Y8N4T": 190,
    "R5B7Q3": 175,
    "9C4M1H": 160,
    SKU_HAIR_ALT: 155,
    "3G7P2W": 140,
    "E4N8J1": 140,
    SKU_ANTICASPA: 70,
    "V2L9D6": 60,
}

# Extra units on 01–24/08 so monthly ranking differs from the 7-day ranking.
UNITS_REST: dict[str, int] = {
    SKU_CLASH: 2500,
    SKU_ANTICASPA: 900,
    "G7Q2D4": 800,
    "M9D3K7": 400,
}


def daterange(start: date, end: date) -> list[date]:
    """Return inclusive calendar dates from ``start`` to ``end``."""
    days: list[date] = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def split_across_days(total: int, n_days: int) -> list[int]:
    """Distribute ``total`` as evenly as possible; remainder goes to earlier days.

    Args:
        total: Units to allocate (exact sum of the result).
        n_days: Number of calendar days.

    Returns:
        One integer per day, summing to ``total``.
    """
    if n_days <= 0:
        raise ValueError("n_days must be positive")
    base, remainder = divmod(total, n_days)
    return [base + (1 if day_index < remainder else 0) for day_index in range(n_days)]


def catalog_by_sku() -> dict[str, dict[str, Any]]:
    """Map SKU code to catalog row (insertion order of ``CATALOG``)."""
    return {row["cod_sku"]: row for row in CATALOG}


def catalog_records() -> list[dict[str, Any]]:
    """Return catalog rows in stable field order for CSV and SQLite."""
    return [{field: row[field] for field in CATALOG_FIELDS} for row in CATALOG]


def generate_sales() -> list[dict[str, Any]]:
    """Build daily sales for August 2026 with a planted 7-day vs month gap.

    Allocation is fully determined by ``UNITS_7D``, ``UNITS_REST``,
    ``UNITS_REST_DEFAULT`` and even day splits. Calling twice yields identical rows.

    Returns:
        One row per (date, sku) with ``qt_sold`` >= 0, stable order.
    """
    skus = list(catalog_by_sku())
    window_days = daterange(WINDOW_START, WINDOW_END)
    rest_days = daterange(SALES_START, WINDOW_START - timedelta(days=1))
    sales: dict[tuple[date, str], int] = {}

    for sku in skus:
        window_parts = split_across_days(UNITS_7D[sku], len(window_days))
        for day, qty in zip(window_days, window_parts):
            sales[(day, sku)] = qty
        rest_total = UNITS_REST.get(sku, UNITS_REST_DEFAULT)
        rest_parts = split_across_days(rest_total, len(rest_days))
        for day, qty in zip(rest_days, rest_parts):
            sales[(day, sku)] = qty

    return [
        {"date": day.isoformat(), "cod_sku": sku, "qt_sold": sales[(day, sku)]}
        for day in daterange(SALES_START, SALES_END)
        for sku in skus
    ]


def build_dataset() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Single snapshot used by both CSV and SQLite writers."""
    return catalog_records(), generate_sales()


def units_in_window(sales_rows: list[dict[str, Any]]) -> dict[str, int]:
    """Sum ``qt_sold`` per SKU inside the frozen 7-day window."""
    totals: dict[str, int] = {sku: 0 for sku in catalog_by_sku()}
    start = WINDOW_START.isoformat()
    end = WINDOW_END.isoformat()
    for row in sales_rows:
        if start <= row["date"] <= end:
            totals[row["cod_sku"]] += int(row["qt_sold"])
    return totals


def gold_top_n(
    sales_rows: list[dict[str, Any]],
    *,
    category: str,
    brand: str | None = None,
    n: int = 5,
) -> list[dict[str, Any]]:
    """Deterministic Top-N: units_7d DESC, then ``cod_sku`` ASC.

    Args:
        sales_rows: Daily sales rows with ``date``, ``cod_sku``, ``qt_sold``.
        category: Catalog category to keep.
        brand: If set, keep only this brand.
        n: Maximum rank length.

    Returns:
        Ranked catalog rows with an extra ``units_7d`` field.
    """
    catalog = catalog_by_sku()
    totals = units_in_window(sales_rows)
    candidates: list[dict[str, Any]] = []
    for sku, meta in catalog.items():
        if meta["category"] != category:
            continue
        if brand is not None and meta["brand"] != brand:
            continue
        item = dict(meta)
        item["units_7d"] = totals[sku]
        candidates.append(item)
    candidates.sort(key=lambda r: (-r["units_7d"], r["cod_sku"]))
    return candidates[:n]


def gold_top_n_diverse(
    sales_rows: list[dict[str, Any]],
    *,
    category: str,
    brand: str | None = None,
    n: int = 5,
) -> list[dict[str, Any]]:
    """Top-N by ``units_7d`` with ``n_brands >= 2`` when alternatives exist in-window.

    When the popularity Top-N is single-brand but the category has other brands with
    positive window sales, swap the lowest-ranked slot for the best-ranked SKU from
    another brand, then re-sort by ``units_7d`` DESC and ``cod_sku`` ASC.

    Args:
        sales_rows: Daily sales rows with ``date``, ``cod_sku``, ``qt_sold``.
        category: Catalog category to keep.
        brand: If set, same as ``gold_top_n`` (brand filter; no diversity swap).
        n: Maximum rank length.

    Returns:
        Ranked catalog rows with an extra ``units_7d`` field.
    """
    if brand is not None:
        return gold_top_n(sales_rows, category=category, brand=brand, n=n)

    catalog = catalog_by_sku()
    totals = units_in_window(sales_rows)
    brands_with_sales = {
        meta["brand"]
        for sku, meta in catalog.items()
        if meta["category"] == category and totals[sku] > 0
    }
    if len(brands_with_sales) < 2:
        return gold_top_n(sales_rows, category=category, n=n)

    top = gold_top_n(sales_rows, category=category, n=n)
    if len({row["brand"] for row in top}) >= 2:
        return top

    dominant_brand = top[0]["brand"]
    top_skus = {row["cod_sku"] for row in top}
    alt_candidates: list[dict[str, Any]] = []
    for sku, meta in catalog.items():
        if meta["category"] != category or meta["brand"] == dominant_brand:
            continue
        if totals[sku] <= 0 or sku in top_skus:
            continue
        item = dict(meta)
        item["units_7d"] = totals[sku]
        alt_candidates.append(item)

    if not alt_candidates:
        return top

    alt_candidates.sort(key=lambda row: (-row["units_7d"], row["cod_sku"]))
    merged = top[:-1] + [alt_candidates[0]]
    merged.sort(key=lambda row: (-row["units_7d"], row["cod_sku"]))
    return merged[:n]


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def ensure_csv_files(data_dir: Path | None = None) -> dict[str, Path]:
    """Write catalog, sales, claims and inventory CSVs from in-memory datasets.

    Args:
        data_dir: Output directory. Defaults to ``./data`` beside this file.

    Returns:
        Paths of the written CSV files.
    """
    from recfair.data.claims import CLAIM_FIELDS, claims_records
    from recfair.data.inventory import INVENTORY_FIELDS, inventory_records

    target = data_dir or DATA_DIR
    catalog_rows, sales_rows = build_dataset()
    catalog_path = target / "tb_catalogo.csv"
    sales_path = target / "tb_vendas.csv"
    claims_path = target / "tb_claims.csv"
    inventory_path = target / "tb_inventory.csv"
    _write_csv(catalog_path, catalog_rows, list(CATALOG_FIELDS))
    _write_csv(sales_path, sales_rows, list(SALES_FIELDS))
    _write_csv(claims_path, claims_records(), list(CLAIM_FIELDS))
    _write_csv(inventory_path, inventory_records(), list(INVENTORY_FIELDS))
    return {
        "tb_catalogo": catalog_path,
        "tb_vendas": sales_path,
        "tb_claims": claims_path,
        "tb_inventory": inventory_path,
    }


def write_sqlite(db_path: Path, data_dir: Path | None = None) -> Path:
    """Create SQLite tables from the same in-memory rows written to CSV.

    Args:
        db_path: Destination ``.db`` file.
        data_dir: Directory for the CSV copies (always overwritten).

    Returns:
        Path of the database file.
    """
    from recfair.data.claims import claims_records
    from recfair.data.inventory import inventory_records

    target = data_dir or DATA_DIR
    ensure_csv_files(target)
    catalog_rows, sales_rows = build_dataset()
    claims_rows = claims_records()
    inventory_rows = inventory_records()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE tb_catalogo (
                cod_sku TEXT PRIMARY KEY,
                name_sku TEXT NOT NULL,
                brand TEXT NOT NULL,
                category TEXT NOT NULL,
                base_price REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE tb_vendas (
                date TEXT NOT NULL,
                cod_sku TEXT NOT NULL,
                qt_sold INTEGER NOT NULL,
                PRIMARY KEY (date, cod_sku),
                FOREIGN KEY (cod_sku) REFERENCES tb_catalogo (cod_sku)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE tb_claims (
                cod_sku TEXT NOT NULL,
                claim_type TEXT NOT NULL,
                claim_text TEXT NOT NULL,
                PRIMARY KEY (cod_sku, claim_type),
                FOREIGN KEY (cod_sku) REFERENCES tb_catalogo (cod_sku)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE tb_inventory (
                date TEXT NOT NULL,
                cod_sku TEXT NOT NULL,
                units_available INTEGER NOT NULL,
                is_launch INTEGER NOT NULL,
                is_promo INTEGER NOT NULL,
                PRIMARY KEY (date, cod_sku),
                FOREIGN KEY (cod_sku) REFERENCES tb_catalogo (cod_sku)
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO tb_catalogo (cod_sku, name_sku, brand, category, base_price)
            VALUES (:cod_sku, :name_sku, :brand, :category, :base_price)
            """,
            catalog_rows,
        )
        conn.executemany(
            """
            INSERT INTO tb_vendas (date, cod_sku, qt_sold)
            VALUES (:date, :cod_sku, :qt_sold)
            """,
            sales_rows,
        )
        conn.executemany(
            """
            INSERT INTO tb_claims (cod_sku, claim_type, claim_text)
            VALUES (:cod_sku, :claim_type, :claim_text)
            """,
            claims_rows,
        )
        conn.executemany(
            """
            INSERT INTO tb_inventory (date, cod_sku, units_available, is_launch, is_promo)
            VALUES (:date, :cod_sku, :units_available, :is_launch, :is_promo)
            """,
            inventory_rows,
        )
        conn.commit()
        _assert_sqlite_matches_rows(conn, catalog_rows, sales_rows)
        _assert_claims_inventory(conn, claims_rows, inventory_rows)
    finally:
        conn.close()
    return db_path


def _assert_sqlite_matches_rows(
    conn: sqlite3.Connection,
    catalog_rows: list[dict[str, Any]],
    sales_rows: list[dict[str, Any]],
) -> None:
    """Fail if SQLite contents differ from the in-memory dataset."""
    cat_db = [
        tuple(row)
        for row in conn.execute(
            "SELECT cod_sku, name_sku, brand, category, base_price "
            "FROM tb_catalogo ORDER BY cod_sku"
        )
    ]
    cat_mem = tuple(
        sorted(
            (
                r["cod_sku"],
                r["name_sku"],
                r["brand"],
                r["category"],
                float(r["base_price"]),
            )
            for r in catalog_rows
        )
    )
    sales_db = [
        tuple(row)
        for row in conn.execute(
            "SELECT date, cod_sku, qt_sold FROM tb_vendas ORDER BY date, cod_sku"
        )
    ]
    sales_mem = tuple(sorted((r["date"], r["cod_sku"], int(r["qt_sold"])) for r in sales_rows))
    if cat_db != list(cat_mem) or sales_db != list(sales_mem):
        raise AssertionError("SQLite rows do not match the in-memory catalog/sales")


def _assert_claims_inventory(
    conn: sqlite3.Connection,
    claims_rows: list[dict[str, Any]],
    inventory_rows: list[dict[str, Any]],
) -> None:
    """Fail if claims or inventory tables differ from in-memory rows."""
    claims_db = [
        tuple(row)
        for row in conn.execute(
            "SELECT cod_sku, claim_type, claim_text FROM tb_claims ORDER BY cod_sku, claim_type"
        )
    ]
    claims_mem = tuple(
        sorted((r["cod_sku"], r["claim_type"], r["claim_text"]) for r in claims_rows)
    )
    inv_db = [
        tuple(row)
        for row in conn.execute(
            "SELECT date, cod_sku, units_available, is_launch, is_promo "
            "FROM tb_inventory ORDER BY cod_sku"
        )
    ]
    inv_mem = tuple(
        sorted(
            (
                r["date"],
                r["cod_sku"],
                int(r["units_available"]),
                int(r["is_launch"]),
                int(r["is_promo"]),
            )
            for r in inventory_rows
        )
    )
    if claims_db != list(claims_mem) or inv_db != list(inv_mem):
        raise AssertionError("SQLite claims/inventory do not match in-memory rows")


def print_gold_preview() -> None:
    """Print gold Top-5 per category (debug helper for the E1 notebook)."""
    sales = generate_sales()
    print(f"TODAY={TODAY} window={WINDOW_START}..{WINDOW_END} (TODAY excluded)")
    for category in (CATEGORY_PERFUME_M, CATEGORY_PERFUME_F, CATEGORY_BODY, CATEGORY_HAIR):
        print(f"\n=== {category} ===")
        for rank, row in enumerate(gold_top_n(sales, category=category), start=1):
            print(
                f"  {rank}. {row['cod_sku']} {row['brand']:16} units_7d={row['units_7d']:4} {row['name_sku']}"
            )
    print("\n=== cabelos + Match ===")
    for rank, row in enumerate(gold_top_n(sales, category=CATEGORY_HAIR, brand="Match"), start=1):
        print(f"  {rank}. {row['cod_sku']} units_7d={row['units_7d']} {row['name_sku']}")


def main() -> None:
    """CLI entry: regenerate CSVs and run self-checks."""
    from recfair.data.claims import claims_records

    written = ensure_csv_files()
    for name, path in written.items():
        print(f"wrote {name}: {path}")
    sales = generate_sales()
    assert generate_sales() == sales, "generate_sales must be deterministic"
    assert set(UNITS_7D) == set(catalog_by_sku()), "UNITS_7D must cover every SKU"
    assert set(UNITS_REST) <= set(catalog_by_sku()), "UNITS_REST keys must be catalog SKUs"
    assert units_in_window(sales) == UNITS_7D, "window totals must match UNITS_7D"
    skus = [row["cod_sku"] for row in CATALOG]
    assert len(skus) == len(set(skus)) == 40
    assert all(SKU_PATTERN.fullmatch(sku) for sku in skus)
    masc = gold_top_n(sales, category=CATEGORY_PERFUME_M)
    assert [r["cod_sku"] for r in masc] == ["7K2N9A", "Q4H8L2", "3R1B6M", "5J8P2X", "W9C5TD"]
    assert all(r["brand"] == "Malbec" for r in masc)
    assert masc[3]["units_7d"] == masc[4]["units_7d"] == 210
    assert SKU_CLASH not in {r["cod_sku"] for r in masc}
    body = gold_top_n(sales, category=CATEGORY_BODY)
    assert all(r["brand"] == "Cuide-se Bem" for r in body)
    hair = gold_top_n(sales, category=CATEGORY_HAIR)
    assert all(r["brand"] == "Match" for r in hair)
    assert SKU_ANTICASPA not in {r["cod_sku"] for r in hair}
    hair_div = gold_top_n_diverse(sales, category=CATEGORY_HAIR)
    assert [r["cod_sku"] for r in hair_div] == [
        "F3P9W2",
        "L6K1C8",
        "2Y8N4T",
        "R5B7Q3",
        SKU_HAIR_ALT,
    ]
    assert len({r["brand"] for r in hair_div}) == 2
    body_div = gold_top_n_diverse(sales, category=CATEGORY_BODY)
    assert [r["cod_sku"] for r in body_div] == [
        "24A51X",
        "K8M2Q1",
        "9P3W7C",
        "B7F4L9",
        "Z5C1R8",
    ]
    masc_div = gold_top_n_diverse(sales, category=CATEGORY_PERFUME_M)
    assert [r["cod_sku"] for r in masc_div] == [
        "7K2N9A",
        "Q4H8L2",
        "3R1B6M",
        "5J8P2X",
        "2M7K4F",
    ]
    db_path = written["tb_catalogo"].parent / "recfair_catalog.db"
    write_sqlite(db_path, written["tb_catalogo"].parent)
    assert len(claims_records()) == 200
    print_gold_preview()
    db_path.unlink()


if __name__ == "__main__":
    main()
