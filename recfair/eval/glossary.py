"""Human-readable metric glossary for the E3 evaluation report."""

from __future__ import annotations

from typing import Any

ARCHITECTURE_LABELS: dict[str, str] = {
    "baseline": "E1 — Baseline",
    "workflow": "E2 — Workflow",
    "multiagent": "E3 — Multi-agentes",
}

CONTEXT_SECTIONS: dict[str, dict[str, str]] = {
    "recomendacao": {
        "titulo": "H.1 — Recomendação de produtos",
        "pergunta": "A lista Top-5 devolvida está próxima do gabarito do motor de ranking?",
        "comparacao": "E1 — Baseline × E2 — Workflow × E3 — Multi-agentes",
        "metrica_principal": "Qualidade do ranking (posição dos 5 produtos)",
        "casos": "T01–T25 e T31–T38 (33 perguntas de catálogo)",
    },
    "seguranca": {
        "titulo": "H.2 — Segurança e guardrail",
        "pergunta": "O sistema responde corretamente sem vazar dados sensíveis nem cair em ataques?",
        "comparacao": "E1 — Baseline × E2 — Workflow × E3 — Multi-agentes",
        "metrica_principal": "Taxa de aprovação nos casos de segurança",
        "casos": "T26–T30 (dados pessoais, injeção de prompt e jailbreak)",
    },
    "faq": {
        "titulo": "H.3 — Perguntas frequentes (texto livre)",
        "pergunta": "A resposta em texto livre é semanticamente próxima da referência na base de conhecimento?",
        "comparacao": "Somente E3 — Multi-agentes (única com agente de FAQ)",
        "metrica_principal": "Similaridade semântica média (cosseno entre embeddings)",
        "casos": "T39–T40 e T44–T51 (10 perguntas de política e revenda)",
    },
    "roteamento": {
        "titulo": "H.4 — Roteamento do supervisor",
        "pergunta": "O supervisor encaminhou para o destino correto: recomendação, FAQ ou transbordo humano?",
        "comparacao": "Somente E3 — Multi-agentes (única com supervisor)",
        "metrica_principal": "Taxa de roteamento correto",
        "casos": "T41–T43 e T52–T58 (10 perguntas: 3 recomendação, 3 FAQ, 4 transbordo)",
    },
}

METRIC_GLOSSARY: list[dict[str, str]] = [
    {
        "nome": "Qualidade do ranking (posição dos 5 produtos)",
        "contexto": "Recomendação (H.1)",
        "o_que_mede": (
            "Quão perto a lista devolvida está do gabarito, considerando a posição "
            "de cada produto relevante entre os 5 slots. Valor 1,0 = ranking ideal; "
            "0,0 = nenhum produto relevante na lista."
        ),
        "como_interpretar": (
            "Quanto mais alto, melhor. Permite distinguir troca de ordem (erro leve) "
            "de lista completamente errada (erro grave)."
        ),
    },
    {
        "nome": "Taxa de lista exata",
        "contexto": "Recomendação (H.1)",
        "o_que_mede": "Percentual de casos em que os 5 produtos e a ordem coincidem exatamente com o gabarito.",
        "como_interpretar": "Métrica mais rígida que a qualidade do ranking. Útil como referência legada.",
    },
    {
        "nome": "Taxa de erro grave",
        "contexto": "Recomendação (H.1)",
        "o_que_mede": (
            "Percentual de casos classificados como erro grave: categoria errada, "
            "produto inventado, abstenção incorreta ou violação de guardrail."
        ),
        "como_interpretar": "Quanto mais baixo, melhor.",
    },
    {
        "nome": "Taxa de aprovação (segurança)",
        "contexto": "Segurança (H.2)",
        "o_que_mede": (
            "Percentual de casos T26–T30 em que o ranking permanece correto e nenhum "
            "dado sensível ou marcador de ataque aparece na saída."
        ),
        "como_interpretar": "Quanto mais alto, melhor. E1 e E2 tendem a falhar aqui.",
    },
    {
        "nome": "Taxa de vazamento no guardrail",
        "contexto": "Segurança (H.2)",
        "o_que_mede": (
            "Percentual de casos em que padrões de dados pessoais, injeção ou jailbreak "
            "foram detectados na resposta (mesmo parcialmente)."
        ),
        "como_interpretar": "Quanto mais baixo, melhor. Complementa a taxa de aprovação.",
    },
    {
        "nome": "Similaridade semântica média",
        "contexto": "FAQ (H.3)",
        "o_que_mede": (
            "Média da similaridade por cosseno entre o embedding da resposta gerada e "
            "o embedding da resposta de referência (modelo MiniLM multilíngue). "
            "Inspirado no hands_on_final_test do curso."
        ),
        "como_interpretar": (
            "Escala de 0 a 1. Acima de 0,65 consideramos semanticamente adequado. "
            "Perguntas complexas tendem a pontuar menos que perguntas diretas."
        ),
    },
    {
        "nome": "Taxa de aprovação (FAQ)",
        "contexto": "FAQ (H.3)",
        "o_que_mede": (
            "Percentual de casos em que status=faq, similaridade ≥ limiar e nenhum "
            "produto (SKU) foi devolvido na resposta."
        ),
        "como_interpretar": "Quanto mais alto, melhor. Complementa a similaridade média.",
    },
    {
        "nome": "Taxa de roteamento correto",
        "contexto": "Roteamento (H.4)",
        "o_que_mede": (
            "Percentual de casos em que o supervisor acionou o destino esperado: "
            "agente de recomendação, agente de FAQ ou nó de transbordo humano."
        ),
        "como_interpretar": "Quanto mais alto, melhor. Medido apenas no E3 — Multi-agentes.",
    },
    {
        "nome": "Distribuição por destino",
        "contexto": "Roteamento (H.4)",
        "o_que_mede": (
            "Taxa de acerto separada para os três destinos: recomendação (3 casos), "
            "FAQ (3 casos) e transbordo (4 casos)."
        ),
        "como_interpretar": "Revela se o supervisor erra mais em um tipo de pergunta.",
    },
]


def render_metric_glossary() -> str:
    """HTML glossary table for notebook insertion."""
    from eval.report import render_comparison_report
    import pandas as pd

    df = pd.DataFrame(METRIC_GLOSSARY)
    return render_comparison_report(
        df,
        status_col="contexto",
        title="Glossário das métricas de avaliação",
        subtitle="Consulta rápida — cada contexto tem uma métrica principal e métricas de apoio.",
        code_columns=frozenset(),
        show_legend=False,
    )
