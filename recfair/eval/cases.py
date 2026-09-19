"""Golden-set loading and deterministic intent mapping."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from recfair.config import golden_cases_path
from recfair.schemas.intent import ParsedIntent

_CLAIM_PATTERNS: list[tuple[str, list[str]]] = [
    (r"anticaspa", ["anticaspa"]),
    (r"vegano", ["vegano"]),
    (r"hipoalerg", ["hipoalergênico", "hipoalergenico"]),
    (r"queda", ["queda", "antiqueda"]),
    (r"fixaç|fixac", ["fixação", "fixacao", "alta fixação"]),
    (r"noturn", ["noturna", "noturno"]),
    (r"promoç|promoc", ["promoção", "promocao"]),
    (r"lançament|lancament", ["lançamento", "lancamento"]),
    (r"estoque", ["estoque"]),
]


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    """Load frozen golden-set cases."""
    target = path or golden_cases_path()
    return json.loads(target.read_text(encoding="utf-8"))


def golden_revision(cases: list[dict[str, Any]] | None = None) -> str:
    """SHA-256 short hash of the canonical JSON blob."""
    items = cases if cases is not None else load_cases()
    blob = json.dumps(items, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def claim_terms_from_text(text: str) -> list[str]:
    """Extract claim search terms from user text."""
    lowered = text.lower()
    terms: list[str] = []
    for pattern, values in _CLAIM_PATTERNS:
        if re.search(pattern, lowered):
            terms.extend(values)
    return list(dict.fromkeys(terms))


def intent_from_case(case: dict[str, Any]) -> ParsedIntent:
    """Map a golden case to a ParsedIntent for the scoring engine."""
    familia = case.get("familia", "")
    if familia == "S_abstain":
        return ParsedIntent(
            abstain=True,
            abstain_reason=case.get("expected_reason"),
        )

    entrada = case.get("entrada") or ""
    if case.get("turns"):
        entrada = case["turns"][-1]

    explicit_terms = case.get("claim_terms")
    if explicit_terms:
        claim_terms = list(explicit_terms)
    else:
        claim_terms = claim_terms_from_text(entrada)

    return ParsedIntent(
        category=case.get("category"),
        brand=case.get("brand"),
        max_price_brl=case.get("max_price_brl"),
        claim_terms=claim_terms,
        require_diversity=bool(case.get("require_diversity")),
    )
