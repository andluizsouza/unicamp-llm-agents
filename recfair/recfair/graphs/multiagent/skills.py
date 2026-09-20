"""Inline skill catalog (no separate ``recfair/skills`` package)."""

from __future__ import annotations

from typing import Any

SKILLS: dict[str, dict[str, Any]] = {
    "skill_recommend": {
        "index": "Top-5 por categoria, filtros e claims",
        "tools": ["parse_intent", "score_recommendation"],
        "instruction": (
            "Ranquear o catálogo RecFair. Não responder FAQ nem políticas. "
            "Não transbordar. Usar intent parseado E2 + engine (substring; "
            "fallback semântico só quando substring não acerta em nenhum SKU)."
        ),
    },
    "skill_faq": {
        "index": "FAQ e-commerce e revenda, só com evidência",
        "tools": ["retrieve_faq"],
        "instruction": (
            "Responder políticas com os chunks recuperados. Sem catálogo. "
            "Sem evidência suficiente, sinalizar no_evidence para handoff."
        ),
    },
}


def skills_index() -> str:
    """One-line index consumed by the supervisor (full skill loaded later)."""
    return "\n".join(f"- {name}: {spec['index']}" for name, spec in SKILLS.items())


def load_skill(name: str) -> dict[str, Any]:
    """Return the full skill spec or raise ``KeyError``."""
    return SKILLS[name]
