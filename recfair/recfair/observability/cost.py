"""Token cost estimation."""

from __future__ import annotations

from recfair.config import USD_PER_1M_INPUT_TOKENS, USD_PER_1M_OUTPUT_TOKENS

_USD_PER_INPUT = USD_PER_1M_INPUT_TOKENS / 1_000_000
_USD_PER_OUTPUT = USD_PER_1M_OUTPUT_TOKENS / 1_000_000


def estimate_llm_cost_usd(tokens_in: int | float, tokens_out: int | float) -> float:
    """Estimated LLM cost from token counts."""
    return float(tokens_in) * _USD_PER_INPUT + float(tokens_out) * _USD_PER_OUTPUT
