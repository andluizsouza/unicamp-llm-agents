"""Parsed user intent shared by eval gold and workflow runtime."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AbstainReason = Literal["missing_category", "unknown_category", "unknown_brand"]


class ParsedIntent(BaseModel):
    """Structured filters extracted from NL or golden-case metadata."""

    category: str | None = None
    brand: str | None = None
    max_price_brl: float | None = None
    claim_terms: list[str] = Field(default_factory=list)
    require_diversity: bool = False
    abstain: bool = False
    abstain_reason: AbstainReason | None = None
