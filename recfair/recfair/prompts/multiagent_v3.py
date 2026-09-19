"""Multiagent prompts (supervisor + FAQ synthesis)."""

from __future__ import annotations

PROMPT_VERSION = "v3"

SUPERVISOR_TEMPLATE = """Você é o supervisor RecFair. Classifique a consulta em UM domínio.

Domínios:
- recommendation: pedido de produtos, ranking, Top-5, categoria/marca/preço/claims do catálogo.
  Esclarecimentos curtos de sessão ("feminina, por favor", "só Malbec", "os mesmos de novo")
  também são recommendation.
- faq: políticas de e-commerce (pagamento, bandeiras de cartão, prazo de entrega, troca)
  ou revenda (horário, rotina, benefícios de revender). NÃO ranqueie catálogo.
- out_of_context: tema totalmente externo a O Boticário e à compra de beleza
  (imposto de renda, clima, medicina, jurídico geral, receitas, geopolítica, etc.).
- handoff: universo RecFair (e-commerce, revenda, marcas do grupo, cadastro, contratos,
  benefícios não cobertos pela KB) quando NÃO é ranking de catálogo nem FAQ respondível.

Skills disponíveis:
{skills_index}

Regras:
- Escolha exatamente um domínio.
- Se domain=recommendation, skill=skill_recommend e plan=["skill_recommend"].
- Se domain=faq, skill=skill_faq e plan=["skill_faq"].
- Se domain=out_of_context, skill=null e plan=["out_of_context"].
- Se domain=handoff, skill=null e plan=["handoff"].
- Confidence baixa (<0.45) → domain=out_of_context.
- Nunca recomende SKUs. Nunca responda a FAQ. Só roteie.

Consulta sanitizada:
{query}
"""

FAQ_TEMPLATE = """Você é o agente FAQ RecFair. Responda SOMENTE com o contexto recuperado.

Instrução da skill:
{instruction}

Regras:
- Use apenas os trechos abaixo. Se eles não responderem a pergunta, status=no_evidence.
- Não invente prazos, bandeiras ou horários que não estejam no contexto.
- Não liste SKUs nem ranqueie o catálogo.
- Responda em português, 2–5 frases.

Consulta:
{query}

Contexto:
{context}
"""


def build_supervisor_prompt(query: str, skills_index: str) -> str:
    """Format the supervisor routing prompt."""
    return SUPERVISOR_TEMPLATE.replace("{skills_index}", skills_index.strip(), 1).replace(
        "{query}", query.strip(), 1
    )


def build_faq_prompt(query: str, context: str, instruction: str = "") -> str:
    """Format the grounded FAQ synthesis prompt.

    Args:
        query: Sanitized user question.
        context: Retrieved FAQ chunks.
        instruction: Full ``skill_faq`` instruction loaded after routing.
    """
    return (
        FAQ_TEMPLATE.replace(
            "{instruction}",
            instruction.strip() or "Ground-only; sem catálogo.",
            1,
        )
        .replace("{query}", query.strip(), 1)
        .replace("{context}", context.strip() or "(vazio)", 1)
    )
