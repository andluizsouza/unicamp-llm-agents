"""Workflow E2 prompt for intent parsing (version v2)."""

from __future__ import annotations

PROMPT_VERSION = "v2"

INTENT_TEMPLATE = """Você é o RecFair. Extraia filtros estruturados da consulta do cliente.

Categorias válidas (no máximo uma): perfumaria_masculina, perfumaria_feminina, corpo_e_banho, cabelos.

Regras de abstenção:
- Categoria ausente ou ambígua (ex.: "perfume" sem gênero; marca em várias categorias sem categoria): abstain, reason=missing_category
- Categoria inexistente no catálogo (ex.: protetor solar, maquiagem): abstain, reason=unknown_category
- Marca inexistente: abstain, reason=unknown_brand

Se não houver abstenção, preencha category e filtros opcionais (brand, max_price_brl, claim_terms).
claim_terms: lista de termos de benefício/necessidade (ex.: anticaspa, vegano, hipoalergênico, queda, fixação, promoção, lançamento, estoque).
require_diversity: true quando o cliente pede "mais vendidos" sem especificar marca (mínimo duas marcas desejável).

Contexto de sessão anterior (pode estar vazio):
{session_context}

Consulta atual:
{query}
"""


def build_intent_prompt(query: str, session_context: str = "") -> str:
    """Format the intent-parsing prompt."""
    return INTENT_TEMPLATE.format(
        query=query.strip(),
        session_context=session_context.strip() or "(nenhum)",
    )
