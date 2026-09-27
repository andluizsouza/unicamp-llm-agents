"""E4 eval helpers: Wilson, weighted metric, min-pairs, frozen ruler (no LLM)."""

from __future__ import annotations

from eval.cases import FROZEN_RULER_MAX_ID, intent_from_case, is_frozen_ruler_case, load_cases
from eval.ethics import (
    CONSEQUENCE_MATRIX,
    count_hedges,
    diferenca_relevante,
    gold_case_for_pair,
    harm_weight,
    load_min_pairs,
    measure_dimensions,
    metrica_ponderada,
    simple_accuracy,
)
from eval.fingerprint import golden_revision
from eval.gold import gold_for
from eval.report.e4_panels import consequence_matrix_table, wilson_overlap_table
from eval.stats import intervalo_wilson, sobrepoe
from recfair.graphs.registry import list_architectures
from recfair.schemas.output import RecFairOutput


def test_frozen_ruler_is_t01_t60() -> None:
    cases = load_cases()
    ids = {case["id"] for case in cases}
    assert "T01" in ids
    assert "T60" in ids
    assert "T61" not in ids
    assert is_frozen_ruler_case({"id": "T61"}) is False
    assert is_frozen_ruler_case({"id": "T60"}) is True
    frozen = [case for case in cases if is_frozen_ruler_case(case)]
    assert len(frozen) == FROZEN_RULER_MAX_ID == 60
    assert len(cases) == 60


def test_golden_revision_matches_e3_set() -> None:
    revision = golden_revision()
    assert len(revision) == 16
    assert revision == "3cbcb3e4c4b9cec7"


def test_wilson_known_values() -> None:
    lo, hi = intervalo_wilson(8, 10)
    assert 0.4 < lo < 0.8 < hi < 1.0
    assert sobrepoe((0.1, 0.5), (0.4, 0.9)) is True
    assert sobrepoe((0.0, 0.2), (0.3, 0.5)) is False


def test_hedges_and_dimensions() -> None:
    assert count_hedges("Talvez confirme com a loja, depende.") >= 2
    output = RecFairOutput(
        status="faq",
        halt_reason="completed",
        answer_text="Talvez o prazo seja 3 dias.",
        citations=["faq.pdf: prazo de 3 dias úteis"],
    )
    dims = measure_dimensions(output, {"aprovado": True, "ndcg_at_5": None})
    assert dims["evidencia"] == 1
    assert dims["ressalvas"] >= 1
    assert dims["acerto"] is True


def test_diferenca_relevante_respects_noise() -> None:
    left = {"acerto": 1, "confianca": 0.9, "evidencia": 3, "ressalvas": 0, "ndcg_at_5": 1.0}
    right = {"acerto": 1, "confianca": 0.91, "evidencia": 3, "ressalvas": 0, "ndcg_at_5": 1.0}
    noise = {
        "confianca": 0.05,
        "evidencia": 1,
        "ressalvas": 1,
        "ndcg_at_5": 0.05,
        "acerto": 0,
    }
    mild = diferenca_relevante(left, right, noise=noise)
    assert mild["relevante"] is False
    right2 = {**right, "ressalvas": 4}
    sharp = diferenca_relevante(left, right2, noise=noise)
    assert sharp["relevante"] is True


def test_metrica_ponderada_orders_grave_worse() -> None:
    good = {
        "case": {"id": "T01", "familia": "S_exact"},
        "check": {"aprovado": True, "severity": "none"},
        "output": {},
    }
    bad = {
        "case": {"id": "T02", "familia": "S_exact"},
        "check": {"aprovado": False, "severity": "grave"},
        "output": {},
    }
    mixed = metrica_ponderada([good, bad], frozen_only=False)
    perfect = metrica_ponderada([good, good], frozen_only=False)
    assert mixed["score"] < perfect["score"]
    simple = simple_accuracy([good, bad], frozen_only=False)
    assert simple["acertos"] == 1
    assert simple["total"] == 2


def test_harm_weight_degraded_pass() -> None:
    check = {"aprovado": True, "severity": "none"}
    assert harm_weight(check, {"familia": "S_exact"}, {"degraded": True}) == 1


def test_min_pairs_catalog() -> None:
    pairs = load_min_pairs()
    axes = {pair["axis"] for pair in pairs}
    assert axes == {"gender", "hair", "age", "register"}
    assert any(pair["layer"] == "quality_parity" for pair in pairs)
    assert any(pair["axis"] == "hair" and pair["layer"] == "identity" for pair in pairs)
    assert any(pair["axis"] == "hair" and pair["layer"] == "quality_parity" for pair in pairs)
    for pair in pairs:
        assert len(pair["variants"]) >= 4


def test_min_pairs_identical_gold() -> None:
    for pair in load_min_pairs():
        shared = gold_case_for_pair(pair)
        expected = gold_for(shared)
        assert expected, pair["pair_id"]
        golds = {tuple(gold_for(shared)) for _ in pair["variants"]}
        assert golds == {tuple(expected)}

    hair_identity = next(
        p for p in load_min_pairs() if p["axis"] == "hair" and p["layer"] == "identity"
    )
    shared = gold_case_for_pair(hair_identity)
    assert intent_from_case(shared).claim_terms == []
    cacheado = next(v for v in hair_identity["variants"] if v["label"] == "cacheado")
    leaked = intent_from_case({**shared, "entrada": cacheado["entrada"]})
    assert "cacheado" in leaked.claim_terms


def test_consequence_matrix_matches_weights() -> None:
    table = consequence_matrix_table()
    assert not table.empty
    assert set(table["gravidade"]) <= {1, 2, 3, 4, 5}
    assert max(row["gravidade"] for row in CONSEQUENCE_MATRIX) == 5


def test_wilson_overlap_table() -> None:
    import pandas as pd

    df = pd.DataFrame(
        [
            {"arch": "a", "lower_limit": 0.1, "upper_limit": 0.4},
            {"arch": "b", "lower_limit": 0.35, "upper_limit": 0.8},
        ]
    )
    overlap = wilson_overlap_table(df)
    assert bool(overlap.iloc[0]["sobrepoe"]) is True


def test_resilient_registered() -> None:
    assert "resilient" in list_architectures()
    assert "multiagent" in list_architectures()
    assert "baseline" in list_architectures()
