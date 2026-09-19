"""Stable structured output schema for all architectures."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from recfair.config import N_RECOMMEND


class RecommendationItem(BaseModel):
    """One recommended SKU in the vitrine."""

    sku: str
    name: str
    brand: str
    category: str
    units_7d: int
    price_brl: float | None = None
    in_stock: bool | None = None
    is_launch: bool | None = None
    is_promo: bool | None = None
    explanation: str | None = None
    citations: list[str] | None = None
    fairness_notes: str | None = None


class RecFairOutput(BaseModel):
    """Top-level agent response contract.

    ``faq`` and ``handoff`` are additive E3 statuses. Ranking cases (T01–T38)
    still use ``recommendation`` / ``abstention`` with the same item contract.
    """

    status: Literal["recommendation", "abstention", "faq", "handoff", "out_of_context"]
    items: list[RecommendationItem] = Field(default_factory=list)
    reason: Literal["missing_category", "unknown_category", "unknown_brand"] | None = None
    halt_reason: Literal["completed", "abstained", "schema_invalid", "recursion_limit"]
    answer_text: str | None = None
    handoff_phone: str | None = None
    agents_route: list[str] = Field(default_factory=list)

    @field_validator("items")
    @classmethod
    def _five_or_empty(cls, items: list[RecommendationItem]) -> list[RecommendationItem]:
        if items and len(items) != N_RECOMMEND:
            raise ValueError(f"recommendation must have exactly {N_RECOMMEND} items")
        return items


RecFairOutput.model_rebuild()
