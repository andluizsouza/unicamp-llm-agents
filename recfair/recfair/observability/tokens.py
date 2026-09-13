"""Token usage extraction from LLM responses."""

from __future__ import annotations

from typing import Any


def usage_from_response(raw: Any) -> tuple[int | None, int | None]:
    """Extract input/output token counts from a LangChain/Gemini response."""
    meta = getattr(raw, "usage_metadata", None) or {}
    if not isinstance(meta, dict):
        return (
            getattr(meta, "input_tokens", None),
            getattr(meta, "output_tokens", None),
        )
    return meta.get("input_tokens"), meta.get("output_tokens")
