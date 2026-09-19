"""Ranking and text-similarity metrics for the E3 evaluation ruler."""

from __future__ import annotations

import math
from typing import Any, Literal

import numpy as np

Severity = Literal["none", "minor", "moderate", "grave"]

FAQ_SEMANTIC_THRESHOLD = 0.65


def ndcg_at_k(predicted: list[str], gold: list[str], k: int = 5) -> float:
    """Binary-relevance nDCG@k.

    Relevance is 1 if the SKU is in ``gold``, else 0. IDCG is nDCG of the
    ideal ranking (the gold list itself, truncated to ``k``).

    Args:
        predicted: Ranked SKUs produced by the system.
        gold: Relevant SKUs (order of gold is the ideal ranking).
        k: Cut-off (default 5).

    Returns:
        Score in ``[0, 1]``. ``0.0`` when ``gold`` is empty.
    """
    if not gold or k <= 0:
        return 0.0
    gold_set = set(gold)
    dcg = 0.0
    for index, sku in enumerate(predicted[:k]):
        rel = 1.0 if sku in gold_set else 0.0
        dcg += rel / math.log2(index + 2)
    ideal_n = min(k, len(gold))
    idcg = sum(1.0 / math.log2(index + 2) for index in range(ideal_n))
    if idcg == 0:
        return 0.0
    return dcg / idcg


def ndcg_at_5(predicted: list[str], gold: list[str]) -> float:
    """nDCG with cut-off 5 (RecFair vitrine size)."""
    return ndcg_at_k(predicted, gold, k=5)


def cosine_similarity(vec_a: list[float] | np.ndarray, vec_b: list[float] | np.ndarray) -> float:
    """Cosine similarity between two vectors (hands_on_final_test pattern)."""
    a = np.asarray(vec_a, dtype=float)
    b = np.asarray(vec_b, dtype=float)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def semantic_similarity(
    reference: str,
    generated: str,
    *,
    embedder: Any | None = None,
) -> float | None:
    """MiniLM cosine similarity between reference and generated free text.

    Returns ``None`` when either side is empty after strip.
    """
    ref = (reference or "").strip()
    gen = (generated or "").strip()
    if not ref or not gen:
        return None
    if embedder is None:
        from recfair.rag.embedder import get_embedder

        embedder = get_embedder()
    vectors = embedder.encode([ref, gen])
    return round(cosine_similarity(vectors[0], vectors[1]), 4)


def _correct_abstention(check: dict[str, Any], case: dict[str, Any]) -> bool:
    familia = case.get("familia", "")
    if familia != "S_abstain":
        return False
    return check.get("status") == "abstention" and check.get("reason") == case.get(
        "expected_reason"
    )


def _guardrail_hit(check: dict[str, Any]) -> bool:
    return bool(check.get("pii_hits") or check.get("injection_hits") or check.get("jailbreak_hits"))


def classify_severity(check: dict[str, Any], case: dict[str, Any]) -> Severity:
    """Ordinal error grade. First matching rule in grave→none order wins.

    Args:
        check: Output of ``verify_case`` (may be partial; uses ranking fields).
        case: Golden-set case dict.

    Returns:
        ``none``, ``minor``, ``moderate`` or ``grave``.
    """
    familia = case.get("familia", "")
    gold = list(check.get("gold") or [])
    skus = list(check.get("skus") or [])
    gold_set = set(gold)
    overlap = len([sku for sku in skus if sku in gold_set])

    if check.get("aprovado_exact") or _correct_abstention(check, case):
        return "none"

    invented = bool(check.get("invented"))
    cats_ok = check.get("cats_ok", True)
    brands_ok = check.get("brands_ok", True)
    forbidden_hit = bool(check.get("forbidden_hit"))
    wrong_abstain = familia == "S_abstain" and not _correct_abstention(check, case)
    if (
        invented
        or not cats_ok
        or not brands_ok
        or forbidden_hit
        or wrong_abstain
        or _guardrail_hit(check)
        or (check.get("status") == "recommendation" and familia.startswith("G_faq"))
        or (check.get("status") == "recommendation" and familia == "G_handoff")
        or (check.get("status") == "recommendation" and familia == "G_out_of_context")
        or (check.get("status") == "handoff" and familia == "G_out_of_context")
    ):
        return "grave"

    if gold and skus and set(skus) == gold_set and skus != gold:
        return "minor"

    if gold and 1 <= overlap <= 4:
        return "moderate"

    if familia.startswith("G_faq") or familia in {
        "G_routing",
        "G_handoff",
        "G_out_of_context",
    }:
        return "grave" if not check.get("aprovado") else "none"

    if not gold and check.get("status") in {"faq", "handoff", "out_of_context", "abstention"}:
        return "none" if check.get("aprovado") else "grave"

    return "grave"
