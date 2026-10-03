"""Recommendation output carries inventory flags and a score explanation."""

from __future__ import annotations

from recfair.graphs.workflow.nodes.scoring import (
    _inventory_flags,
    abstain_node,
    scoring_node,
    synthesize_node,
)
from recfair.schemas.intent import ParsedIntent


def test_synthesize_fills_stock_launch_promo_and_explanation() -> None:
    intent = ParsedIntent(
        category="cabelos",
        require_diversity=True,
        claim_terms=["frizz"],
    )
    scored = scoring_node({"parsed_intent": intent})
    update = synthesize_node({**scored, "parsed_intent": intent})
    output = update["output"]

    assert output.status == "recommendation"
    assert output.answer_text is not None
    assert "cabelos" in output.answer_text
    assert output.reason is None

    by_sku = {item.sku: item for item in output.items}
    assert "3G7P2W" in by_sku
    promo = by_sku["3G7P2W"]
    assert promo.in_stock is True
    assert promo.is_launch is False
    assert promo.is_promo is True
    assert promo.explanation is not None
    assert "is_promo+" in promo.explanation
    assert "pontos=" in promo.explanation

    for item in output.items:
        assert item.in_stock is not None
        assert item.is_launch is not None
        assert item.is_promo is not None
        assert item.explanation
        assert "frizz" not in item.explanation.lower()
        assert item.fairness_notes is None


def test_forced_out_of_stock_sku_is_false() -> None:
    update = synthesize_node(
        {
            "ranked_skus": ["E4N8J1", "3G7P2W", "F3P9W2", "L6K1C8", "2Y8N4T"],
            "scoring_trace": [],
            "parsed_intent": ParsedIntent(category="cabelos"),
        }
    )
    first = update["output"].items[0]
    assert first.sku == "E4N8J1"
    assert first.in_stock is False
    assert first.explanation is not None
    assert first.explanation.startswith("pontos=0")


def test_missing_inventory_row_stays_null() -> None:
    assert _inventory_flags(None) == (None, None, None)


def test_abstain_answer_text_follows_reason() -> None:
    output = abstain_node(
        {"parsed_intent": ParsedIntent(abstain=True, abstain_reason="unknown_brand")}
    )["output"]
    assert output.reason == "unknown_brand"
    assert output.answer_text is not None
    assert "marca" in output.answer_text
