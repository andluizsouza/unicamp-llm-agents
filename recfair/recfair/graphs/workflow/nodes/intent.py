"""Intent parsing node for the workflow graph."""

from __future__ import annotations

from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from recfair.config import TEMPERATURE, model_version, sampling_fixed_by_model
from recfair.graphs.workflow.state import WorkflowState
from recfair.observability.tokens import usage_from_response
from recfair.prompts.workflow_v2 import build_intent_prompt
from recfair.schemas.intent import ParsedIntent

_LLM: ChatGoogleGenerativeAI | None = None
_STRUCTURED: Any = None


class IntentExtraction(BaseModel):
    """LLM structured output for intent parsing."""

    abstain: bool = False
    abstain_reason: str | None = None
    category: str | None = None
    brand: str | None = None
    max_price_brl: float | None = None
    claim_terms: list[str] = Field(default_factory=list)
    require_diversity: bool = False


def _get_structured_llm() -> Any:
    global _LLM, _STRUCTURED
    if _STRUCTURED is None:
        mv = model_version()
        kwargs: dict[str, Any] = {"model": mv}
        if not sampling_fixed_by_model(mv):
            kwargs["temperature"] = TEMPERATURE
        _LLM = ChatGoogleGenerativeAI(**kwargs)
        _STRUCTURED = _LLM.with_structured_output(
            IntentExtraction,
            include_raw=True,
            method="json_schema",
        )
    return _STRUCTURED


def _session_context(state: WorkflowState) -> str:
    prior = state.get("session_intent") or {}
    if not prior:
        return ""
    parts = []
    for key in ("category", "brand", "max_price_brl", "claim_terms", "require_diversity"):
        if key in prior and prior[key] is not None:
            parts.append(f"{key}={prior[key]}")
    return "; ".join(parts)


def _merge_intent(session: dict[str, Any], extracted: IntentExtraction) -> ParsedIntent:
    category = extracted.category or session.get("category")
    brand = extracted.brand or session.get("brand")
    max_price = extracted.max_price_brl
    if max_price is None:
        max_price = session.get("max_price_brl")
    claim_terms = list(extracted.claim_terms or [])
    if not claim_terms:
        claim_terms = list(session.get("claim_terms") or [])
    require_diversity = extracted.require_diversity or bool(session.get("require_diversity"))
    if extracted.abstain:
        reason = extracted.abstain_reason
        if reason not in {"missing_category", "unknown_category", "unknown_brand"}:
            reason = "missing_category"
        return ParsedIntent(abstain=True, abstain_reason=reason)
    return ParsedIntent(
        category=category,
        brand=brand,
        max_price_brl=max_price,
        claim_terms=claim_terms,
        require_diversity=require_diversity,
    )


def _unpack_intent_response(packed: Any) -> tuple[IntentExtraction, int | None, int | None]:
    if isinstance(packed, dict) and "parsed" in packed:
        tokens_in, tokens_out = usage_from_response(packed.get("raw"))
        return packed["parsed"], tokens_in, tokens_out
    return packed, None, None


def parse_intent_node(state: WorkflowState) -> dict[str, Any]:
    """Parse NL query into ParsedIntent, merging session checkpoint."""
    structured = _get_structured_llm()
    prompt = build_intent_prompt(state["query"], _session_context(state))
    extracted, tokens_in, tokens_out = _unpack_intent_response(structured.invoke(prompt))
    parsed = _merge_intent(state.get("session_intent") or {}, extracted)
    session_update = {
        "category": parsed.category,
        "brand": parsed.brand,
        "max_price_brl": parsed.max_price_brl,
        "claim_terms": parsed.claim_terms,
        "require_diversity": parsed.require_diversity,
    }
    return {
        "parsed_intent": parsed,
        "session_intent": session_update,
        "chamadas_llm": state.get("chamadas_llm", 0) + 1,
        "tokens_entrada": state.get("tokens_entrada", 0) + (tokens_in or 0),
        "tokens_saida": state.get("tokens_saida", 0) + (tokens_out or 0),
        "step": state.get("step", 0) + 1,
    }


def route_after_intent(state: WorkflowState) -> str:
    """Conditional edge: abstain or run scoring."""
    intent = state.get("parsed_intent")
    if intent and intent.abstain:
        return "abstain"
    return "score"
