"""Unit tests for substring-first claim matching and semantic fallback."""

from __future__ import annotations

import pytest

from recfair.schemas.intent import ParsedIntent
from recfair.tools.claims_semantic import (
    _substring_match,
    match_substring_or_semantic,
    pool_has_substring_match,
)
from recfair.tools.scoring.engine import _claim_match, score_recommendation

# Paraphrases that fail substring but pass semantic (evaluated here, not in H.1).
SEMANTIC_ORACLES: list[dict[str, object]] = [
    {
        "sku": "24A51X",
        "terms": ["sem ingredientes de origem animal"],
        "category": "corpo_e_banho",
    },
    {
        "sku": "V2L9D6",
        "terms": ["cabelo caindo"],
        "category": "cabelos",
    },
    {
        "sku": "B7F4L9",
        "terms": ["pele reativa"],
        "category": "corpo_e_banho",
    },
]


def test_pool_has_substring_match_positive() -> None:
    pool = ["H8Q3N1", "3G7P2W"]
    assert pool_has_substring_match(pool, ["anticaspa"])


def test_pool_has_substring_match_negative_for_paraphrase() -> None:
    pool = ["24A51X", "K8M2Q1"]
    assert not pool_has_substring_match(pool, ["sem ingredientes de origem animal"])


def test_semantic_fallback_skipped_when_pool_has_substring_hit() -> None:
    intent = ParsedIntent(category="cabelos", claim_terms=["anticaspa"])
    with_substring = score_recommendation(intent)
    with_fallback = score_recommendation(intent, semantic_fallback=True)
    assert with_substring.skus == with_fallback.skus


def test_semantic_fallback_uses_substring_only_when_pool_has_hit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intent = ParsedIntent(category="cabelos", claim_terms=["anticaspa", "queda"])
    monkeypatch.setattr(
        "recfair.tools.claims_semantic.match_substring_or_semantic",
        lambda sku, terms: (_ for _ in ()).throw(
            AssertionError("semantic path should not run when substring hits pool")
        ),
    )
    result = score_recommendation(intent, semantic_fallback=True)
    assert result.skus


def test_match_substring_or_semantic_prefers_substring() -> None:
    assert match_substring_or_semantic("H8Q3N1", ["anticaspa"]) == "anticaspa"


def test_match_substring_or_semantic_falls_back_when_substring_misses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "recfair.tools.claims_semantic._semantic_match_sku",
        lambda sku, terms: "sem ingredientes de origem animal" if sku == "24A51X" else None,
    )
    assert _claim_match("24A51X", ["sem ingredientes de origem animal"]) is None
    assert (
        match_substring_or_semantic("24A51X", ["sem ingredientes de origem animal"])
        == "sem ingredientes de origem animal"
    )


@pytest.fixture(scope="module")
def claims_index_ready() -> None:
    from recfair.rag.store import indexes_dir
    from recfair.tools.claims_semantic import build_claims_index

    meta = indexes_dir() / "claims.json"
    if not meta.is_file():
        build_claims_index()


@pytest.mark.usefixtures("claims_index_ready")
@pytest.mark.parametrize("oracle", SEMANTIC_ORACLES, ids=[str(o["sku"]) for o in SEMANTIC_ORACLES])
def test_semantic_oracle_paraphrase_matches_sku(oracle: dict[str, object]) -> None:
    sku = str(oracle["sku"])
    terms = [str(item) for item in oracle["terms"]]
    assert _substring_match(sku, terms) is None
    assert match_substring_or_semantic(sku, terms) is not None


@pytest.mark.usefixtures("claims_index_ready")
@pytest.mark.parametrize(
    "sku,category,terms",
    [
        ("24A51X", "corpo_e_banho", ["sem ingredientes de origem animal"]),
        ("B7F4L9", "corpo_e_banho", ["pele reativa"]),
    ],
)
def test_semantic_oracle_ranks_target_in_top5(
    sku: str, category: str, terms: list[str]
) -> None:
    intent = ParsedIntent(category=category, claim_terms=terms)
    ranked = score_recommendation(intent, semantic_fallback=True).skus
    assert sku in ranked
