"""Attach source excerpts to RecFairOutput so the user can see the evidence."""

from __future__ import annotations

from typing import Any

from recfair.data.claims import claims_by_sku
from recfair.schemas.output import RecFairOutput, RecommendationItem

_CLAIM_KEYS = ("publico_alvo", "beneficios", "descricao")


def _item_citations(sku: str) -> list[str]:
    blob = claims_by_sku().get(sku) or {}
    cites: list[str] = []
    for key in _CLAIM_KEYS:
        text = (blob.get(key) or "").strip()
        if text:
            cites.append(f"{key}: {text}")
    return cites[:3]


def fill_citations(
    output: RecFairOutput,
    *,
    faq_evidence: list[dict[str, Any]] | None = None,
) -> RecFairOutput:
    """Populate ``citations`` from catalog claims or FAQ chunks.

    Existing non-empty item citations are preserved. Empty lists are filled.
    """
    if output.status == "recommendation" and output.items:
        new_items: list[RecommendationItem] = []
        collected: list[str] = []
        for item in output.items:
            cites = list(item.citations or []) or _item_citations(item.sku)
            new_items.append(item.model_copy(update={"citations": cites}))
            collected.extend(cites)
        return output.model_copy(update={"items": new_items, "citations": collected[:15]})
    if output.status == "faq":
        excerpts: list[str] = []
        for hit in faq_evidence or []:
            excerpt = str(hit.get("excerpt") or "").strip()
            source = str(hit.get("source") or "faq")
            if excerpt:
                excerpts.append(f"{source}: {excerpt[:400]}")
        if excerpts:
            return output.model_copy(update={"citations": excerpts})
    return output
