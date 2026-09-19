"""Structured-output LLM factory for multiagent nodes."""

from __future__ import annotations

from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from recfair.config import TEMPERATURE, model_version, sampling_fixed_by_model
from recfair.observability.tokens import usage_from_response


def make_structured_llm(schema: type[BaseModel]) -> Any:
    """ChatGoogleGenerativeAI with JSON-schema structured output."""
    mv = model_version()
    kwargs: dict[str, Any] = {"model": mv}
    if not sampling_fixed_by_model(mv):
        kwargs["temperature"] = TEMPERATURE
    llm = ChatGoogleGenerativeAI(**kwargs)
    return llm.with_structured_output(schema, include_raw=True, method="json_schema")


def unpack_structured(packed: Any) -> tuple[Any, int | None, int | None]:
    """Split LangChain ``include_raw`` payload into parsed model + tokens."""
    if isinstance(packed, dict) and "parsed" in packed:
        tokens_in, tokens_out = usage_from_response(packed.get("raw"))
        return packed["parsed"], tokens_in, tokens_out
    return packed, None, None
