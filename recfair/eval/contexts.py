"""Evaluation contexts for the E3 golden-set ruler."""

from __future__ import annotations

from typing import Any, Literal

EvalContext = Literal["recomendacao", "seguranca", "faq", "roteamento"]

EVAL_CONTEXTS: tuple[EvalContext, ...] = (
    "recomendacao",
    "seguranca",
    "faq",
    "roteamento",
)

CONTEXT_LABELS: dict[EvalContext, str] = {
    "recomendacao": "Recomendação de produtos",
    "seguranca": "Segurança e guardrail",
    "faq": "Perguntas frequentes (texto livre)",
    "roteamento": "Roteamento do supervisor",
}

CONTEXT_ARCHITECTURES: dict[EvalContext, tuple[str, ...]] = {
    "recomendacao": ("baseline", "workflow", "multiagent"),
    "seguranca": ("baseline", "workflow", "multiagent"),
    "faq": ("multiagent",),
    "roteamento": ("multiagent",),
}

_FAMILIA_CONTEXT: dict[str, EvalContext] = {
    "G_pii": "seguranca",
    "G_injection": "seguranca",
    "G_jailbreak": "seguranca",
    "G_faq_ecommerce": "faq",
    "G_faq_revenda": "faq",
    "G_routing": "roteamento",
    "G_handoff": "roteamento",
    "G_out_of_context": "roteamento",
}


def eval_context_of(case: dict[str, Any]) -> EvalContext:
    """Return the evaluation context for a golden case.

    Prefers explicit ``contexto`` on the case; falls back to ``familia`` / id.
    """
    explicit = case.get("contexto")
    if explicit in EVAL_CONTEXTS:
        return explicit
    familia = case.get("familia", "")
    if familia in _FAMILIA_CONTEXT:
        return _FAMILIA_CONTEXT[familia]
    return "recomendacao"


def filter_records_by_context(
    records: list[dict[str, Any]],
    context: EvalContext,
) -> list[dict[str, Any]]:
    """Subset runner records by evaluation context."""
    return [record for record in records if eval_context_of(record["case"]) == context]


def context_case_summary(cases: list[dict[str, Any]] | None = None) -> dict[str, list[str]]:
    """Map each context to the case ids that belong to it."""
    from eval.fingerprint import load_cases

    items = cases if cases is not None else load_cases()
    summary: dict[str, list[str]] = {ctx: [] for ctx in EVAL_CONTEXTS}
    for case in items:
        summary[eval_context_of(case)].append(case["id"])
    return summary


DEFAULT_FAST_CASE_IDS: tuple[str, ...] = (
    "T01",  # recomendação
    "T26",  # segurança
    "T39",  # FAQ
    "T41",  # roteamento → perguntas frequentes
    "T42",  # roteamento → recomendação
    "T43",  # roteamento → fora de contexto
)


def select_cases_for_fast_run(
    cases: list[dict[str, Any]] | None = None,
    *,
    case_ids: tuple[str, ...] | None = None,
    per_context: int = 1,
) -> list[dict[str, Any]]:
    """Return a small golden-set sample with at least one case per context.

    Args:
        cases: Full golden-set (defaults to ``load_cases()``).
        case_ids: Explicit case ids to run. When omitted, picks ``per_context``
            cases from each evaluation context in stable order.
        per_context: How many cases to keep per context when ``case_ids`` is
            not provided (minimum 1).

    Returns:
        Subset of cases, preserving golden-set order.

    Raises:
        ValueError: When a requested id is missing or a context has no cases.
    """
    from eval.fingerprint import load_cases

    all_cases = cases if cases is not None else load_cases()
    by_id = {case["id"]: case for case in all_cases}
    per_context = max(1, per_context)

    if case_ids is None:
        summary = context_case_summary(all_cases)
        selected_ids: list[str] = []
        for context in EVAL_CONTEXTS:
            bucket = summary[context][:per_context]
            if not bucket:
                raise ValueError(f"context {context!r} has no cases in golden-set")
            selected_ids.extend(bucket)
        case_ids = tuple(selected_ids)

    selected = []
    seen: set[str] = set()
    for case_id in case_ids:
        if case_id not in by_id:
            raise ValueError(f"unknown golden case id: {case_id}")
        if case_id in seen:
            continue
        seen.add(case_id)
        selected.append(by_id[case_id])

    covered = {eval_context_of(case) for case in selected}
    missing = [ctx for ctx in EVAL_CONTEXTS if ctx not in covered]
    if missing:
        labels = ", ".join(CONTEXT_LABELS[ctx] for ctx in missing)
        raise ValueError(f"fast sample missing context(s): {labels}")

    return selected


def routing_destination(case: dict[str, Any]) -> str:
    """Expected routing destination label for a routing-context case."""
    if case.get("familia") == "G_out_of_context":
        return "fora de contexto"
    if case.get("familia") == "G_handoff":
        return "transbordo"
    route = case.get("expected_route")
    if route == "recommendation":
        return "recomendação"
    if route == "faq":
        return "perguntas frequentes"
    return str(route or "—")
