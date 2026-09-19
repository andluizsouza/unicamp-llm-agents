"""Unit tests for the E3 evaluation ruler (no LLM)."""

from __future__ import annotations

from eval.contexts import (
    DEFAULT_FAST_CASE_IDS,
    EVAL_CONTEXTS,
    context_case_summary,
    eval_context_of,
    filter_records_by_context,
    routing_destination,
    select_cases_for_fast_run,
)
from eval.gold import gold_naive_for
from eval.metrics import classify_severity, cosine_similarity, ndcg_at_5, semantic_similarity
from eval.report import summarize_by_context
from eval.requirements import rf_results_for, summarize_by_requirement
from eval.verify import verify_case
from recfair.schemas.output import RecFairOutput, RecommendationItem


def _item(sku: str) -> RecommendationItem:
    return RecommendationItem(
        sku=sku,
        name=sku,
        brand="Match",
        category="cabelos",
        units_7d=1,
    )


def _ranking(skus: list[str]) -> RecFairOutput:
    return RecFairOutput(
        status="recommendation",
        items=[_item(sku) for sku in skus],
        halt_reason="completed",
    )


def test_ndcg_exact_is_one() -> None:
    gold = ["A", "B", "C", "D", "E"]
    assert ndcg_at_5(gold, gold) == 1.0


def test_ndcg_partial_overlap_below_one() -> None:
    gold = ["A", "B", "C", "D", "E"]
    predicted = ["B", "A", "C", "X", "Y"]
    score = ndcg_at_5(predicted, gold)
    assert 0.5 < score < 1.0


def test_ndcg_wrong_category_low() -> None:
    gold = ["A", "B", "C", "D", "E"]
    predicted = ["X", "Y", "Z", "W", "V"]
    assert ndcg_at_5(predicted, gold) == 0.0


def test_severity_none_on_exact() -> None:
    check = {
        "aprovado_exact": True,
        "gold": ["A", "B", "C", "D", "E"],
        "skus": ["A", "B", "C", "D", "E"],
        "invented": [],
        "cats_ok": True,
        "brands_ok": True,
        "forbidden_hit": False,
        "status": "recommendation",
    }
    assert classify_severity(check, {"familia": "S_exact"}) == "none"


def test_severity_minor_order_swap() -> None:
    gold = ["A", "B", "C", "D", "E"]
    predicted = ["B", "A", "C", "D", "E"]
    check = {
        "aprovado_exact": False,
        "gold": gold,
        "skus": predicted,
        "invented": [],
        "cats_ok": True,
        "brands_ok": True,
        "forbidden_hit": False,
        "status": "recommendation",
        "ndcg_at_5": ndcg_at_5(predicted, gold),
    }
    assert classify_severity(check, {"familia": "S_exact"}) == "minor"


def test_severity_moderate_partial() -> None:
    check = {
        "aprovado_exact": False,
        "gold": ["A", "B", "C", "D", "E"],
        "skus": ["A", "B", "C", "X", "Y"],
        "invented": [],
        "cats_ok": True,
        "brands_ok": True,
        "forbidden_hit": False,
        "status": "recommendation",
    }
    assert classify_severity(check, {"familia": "S_exact"}) == "moderate"


def test_severity_grave_wrong_category() -> None:
    check = {
        "aprovado_exact": False,
        "gold": ["A", "B", "C", "D", "E"],
        "skus": ["X", "Y", "Z", "W", "V"],
        "invented": [],
        "cats_ok": False,
        "brands_ok": True,
        "forbidden_hit": False,
        "status": "recommendation",
    }
    assert classify_severity(check, {"familia": "S_window"}) == "grave"


def test_false_positive_gap_flag() -> None:
    from eval.fingerprint import load_cases
    from eval.gold import gold_for

    case = next(item for item in load_cases() if item["id"] == "T25")
    naive = gold_naive_for(case)
    filtered = gold_for(case)
    assert naive != filtered
    output = _ranking(naive)
    check = verify_case(case, output)
    assert check["false_positive_gap"] is True
    assert check["gold_naive"] == naive
    assert check["gap_intentional_pass"] is False


class _MockEmbedder:
    """Deterministic 3-d vectors for semantic-similarity unit tests."""

    def encode(self, texts: list[str]):
        import numpy as np

        vectors = []
        for text in texts:
            lowered = text.lower()
            visa = 1.0 if "visa" in lowered else 0.0
            master = 1.0 if "mastercard" in lowered or "master" in lowered else 0.0
            elo = 1.0 if "elo" in lowered else 0.0
            vectors.append([visa, master, elo])
        arr = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return arr / norms


def test_out_of_context_case_uses_fixed_template() -> None:
    from eval.fingerprint import load_cases
    from recfair.config import OUT_OF_CONTEXT_TEXT

    case = next(item for item in load_cases() if item["id"] == "T59")
    output = RecFairOutput(
        status="out_of_context",
        halt_reason="completed",
        answer_text=OUT_OF_CONTEXT_TEXT,
        agents_route=["security", "supervisor", "out_of_context"],
    )
    check = verify_case(case, output)
    assert check["aprovado"] is True
    assert check["skus"] == []
    assert check["handoff_phone"] is None
    assert check["severity"] == "none"


def test_faq_case_uses_semantic_similarity(monkeypatch) -> None:
    from eval.fingerprint import load_cases

    monkeypatch.setattr("recfair.rag.embedder.get_embedder", lambda: _MockEmbedder())

    case = next(item for item in load_cases() if item["id"] == "T39")
    assert case.get("expected_answer")
    output = RecFairOutput(
        status="faq",
        halt_reason="completed",
        answer_text="Aceitamos Visa, Mastercard, Elo, Hipercard e American Express.",
        agents_route=["security", "supervisor", "faq"],
    )
    check = verify_case(case, output)
    assert check["faq_semantic_similarity"] is not None
    assert check["faq_semantic_similarity"] >= 0.65
    assert check["aprovado"] is True
    assert check["skus"] == []
    assert check["severity"] == "none"


def test_context_mapping_matches_golden_set() -> None:
    from eval.fingerprint import load_cases

    cases = load_cases()
    summary = context_case_summary(cases)
    assert len(summary["recomendacao"]) == 33
    assert len(summary["seguranca"]) == 5
    assert len(summary["faq"]) == 10
    assert len(summary["roteamento"]) == 12
    for case in cases:
        assert eval_context_of(case) in EVAL_CONTEXTS


def test_fast_sample_covers_all_contexts() -> None:
    from eval.fingerprint import load_cases

    cases = load_cases()
    sample = select_cases_for_fast_run(cases, case_ids=DEFAULT_FAST_CASE_IDS)
    assert len(sample) == len(DEFAULT_FAST_CASE_IDS)
    covered = {eval_context_of(case) for case in sample}
    assert covered == set(EVAL_CONTEXTS)


def test_fast_sample_per_context_minimum() -> None:
    from eval.fingerprint import load_cases

    sample = select_cases_for_fast_run(load_cases(), per_context=1)
    assert len(sample) == len(EVAL_CONTEXTS)
    assert {eval_context_of(case) for case in sample} == set(EVAL_CONTEXTS)


def test_routing_destination_split() -> None:
    from eval.fingerprint import load_cases

    cases = [c for c in load_cases() if eval_context_of(c) == "roteamento"]
    destinations = [routing_destination(case) for case in cases]
    assert destinations.count("recomendação") == 3
    assert destinations.count("perguntas frequentes") == 3
    assert destinations.count("fora de contexto") == 4
    assert destinations.count("transbordo") == 2


def test_summarize_by_context_partitions_records() -> None:
    from eval.fingerprint import load_cases

    cases = load_cases()
    records = [
        {
            "case": case,
            "check": {
                "aprovado": True,
                "aprovado_exact": True,
                "ndcg_at_5": 1.0,
                "severity": "none",
                "skus": [],
                "gold": [],
            },
        }
        for case in cases
    ]
    blocks = summarize_by_context(records)
    assert blocks["recomendacao"]["n"] == 33
    assert blocks["seguranca"]["n"] == 5
    assert blocks["faq"]["n"] == 10
    assert blocks["roteamento"]["n"] == 12
    assert blocks["roteamento"]["by_destination"]["fora de contexto"]["n"] == 4
    assert blocks["roteamento"]["by_destination"]["transbordo"]["n"] == 2
    rec_subset = filter_records_by_context(records, "recomendacao")
    assert len(rec_subset) == 33


def test_cosine_similarity_identical_vectors() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_semantic_similarity_same_text() -> None:
    text = "Aceitamos Visa, Mastercard e Elo no site."
    score = semantic_similarity(text, text, embedder=_MockEmbedder())
    assert score is not None
    assert score > 0.99


def test_summarize_rf04_only_on_abstention_cases() -> None:
    records = [
        {
            "check": {
                "rf_results": {
                    "RF-01": True,
                    "RF-04": True,
                    "RF-05": None,
                    "RF-02": None,
                    "RF-03": None,
                    "RF-06": None,
                    "RF-07": None,
                }
            }
        },
        {
            "check": {
                "rf_results": {
                    "RF-01": True,
                    "RF-04": None,
                    "RF-05": None,
                    "RF-02": True,
                    "RF-03": True,
                    "RF-06": None,
                    "RF-07": True,
                }
            }
        },
    ]
    table = summarize_by_requirement(records)
    rf04 = table[table["requisito"] == "RF-04"].iloc[0]
    assert int(rf04["total"]) == 1
    assert int(rf04["passou"]) == 1
    assert rf04["conceito"]


def test_html_status_colors_use_canonical_palette() -> None:
    import pandas as pd

    from eval.report import render_comparison_report

    df = pd.DataFrame(
        [
            {"caso": "T01", "status_final": "sucesso"},
            {"caso": "T06", "status_final": "erro"},
            {"caso": "T16", "status_final": "erro*"},
        ]
    )
    html = render_comparison_report(df, title="cores")
    assert "#198754" in html
    assert "#dc3545" in html
    assert "#fd7e14" in html
    assert "sucesso (restrito ou gap acertado)" in html


def test_context_case_table_uses_status_final() -> None:
    from eval.fingerprint import load_cases
    from eval.report import build_context_case_table

    case = next(item for item in load_cases() if item["id"] == "T01")
    records = [
        {
            "case": case,
            "check": {
                "aprovado": True,
                "skus": [],
                "gold": [],
                "status": "recommendation",
            },
        }
    ]
    table = build_context_case_table(records, "recomendacao")
    assert "status_final" in table.columns
    assert table.iloc[0]["status_final"] == "sucesso"


def test_rf_breakdown_includes_concepts() -> None:
    from eval.requirements import RF_DESCRIPTIONS, summarize_by_requirement

    records = [
        {
            "check": {
                "rf_results": {rf: True for rf in RF_DESCRIPTIONS},
            }
        }
    ]
    table = summarize_by_requirement(records)
    assert "conceito" in table.columns
    assert table["conceito"].str.len().min() > 10


def test_rf04_none_on_ranking_case() -> None:
    check = {
        "status": "recommendation",
        "skus": ["A8T3K5", "H8Q3N1", "2Y8N4T", "3G7P2W", "V2L9D6"],
        "invented": [],
        "cats_ok": True,
        "brands_ok": True,
        "order_match": True,
        "n_brands": 2,
        "forbidden_hit": False,
        "gold": ["A8T3K5", "H8Q3N1", "2Y8N4T", "3G7P2W", "V2L9D6"],
    }
    case = {
        "id": "T01",
        "familia": "S_diversity",
        "category": "cabelos",
        "require_diversity": True,
    }
    results = rf_results_for(case, check)
    assert results["RF-04"] is None
    assert results["RF-07"] is True
