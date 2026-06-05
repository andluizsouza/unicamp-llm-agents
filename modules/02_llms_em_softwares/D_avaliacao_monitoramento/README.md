# Bloco D: Avaliação e Monitoramento de LLMs

## TL;DR / Resumo Executivo
O Bloco D fecha o ciclo de construção de sistemas com LLMs ao mostrar como **medir qualidade, custo e confiabilidade** depois que o modelo já está em uso. Seu objetivo central é ensinar o aluno a avaliar sistemas de IA de forma contextual, combinando métricas automáticas, avaliação humana e julgamento por LLMs, além de implementar **observabilidade** e **monitoramento em produção** para rastrear falhas, degradação silenciosa e mudanças de comportamento ao longo do tempo. Ao final, o aluno entende como comparar modelos, validar pipelines RAG e acompanhar sistemas reais com logs, métricas e tracing.

## Conceitos Fundamentais (Tópicos Abordados)

- **Avaliação Contextual de LLMs**: A qualidade de um sistema depende do caso de uso, equilibrando factualidade, clareza, utilidade, custo e latência.
- **LLM-as-a-Judge**: Uso de um modelo mais capaz para avaliar respostas de outro modelo com critérios estruturados e escala Likert.
- **Métricas Textuais e Semânticas**: Aplicação de BLEU, ROUGE e BERTScore para comparar respostas com referências.
- **Avaliação de RAG**: Uso de Precision@k, Recall@k e Groundedness para medir recuperação e fundamentação da resposta no contexto recuperado.
- **Custo e Performance**: Medição de latência P95, throughput e custo por requisição para decisões de produção.
- **Observabilidade**: Monitoramento de prompts, retrieval, chamadas ao modelo e pós-processamento com logs, métricas e tracing.
- **Drift e Degradação**: Identificação de data drift, concept drift, model drift e document drift em sistemas baseados em LLMs.
- **Ferramentas de Monitoramento**: LangSmith, LangFuse, Weights & Biases e Arize Phoenix como apoio à análise de sistemas em produção.


## **Matriz de Conteúdo**: Aulas do Bloco D

| Aula | Tema Principal | Descrição Curta | Objetivo | Arquivo de Referência |
|------|----------------|----------------|----------|--------|
| 01 | Avaliação de LLMs | Metodologias de avaliação, métricas textuais, LLM-as-a-Judge e comparação entre API e modelo local | Compreender como medir qualidade e custo de sistemas de LLM de acordo com o contexto de uso. | [01_avaliacao_llms.md](/modules/02_llms_em_softwares/D_avaliacao_monitoramento/01_avaliacao_llms.md) |
| 02 | Monitoramento em Produção | Observabilidade, logs, métricas, tracing, groundedness e drift | Aprender a acompanhar sistemas reais e diagnosticar degradações de forma contínua. | [02_monitoramento.md](/modules/02_llms_em_softwares/D_avaliacao_monitoramento/02_monitoramento.md) |
| Prática | Atividade em Notebook | Implementação de métricas de avaliação, LLM-as-a-Judge e análise de groundedness | Aplicar os conceitos de avaliação e monitoramento em um pipeline prático com código. | [hands_on_evaluation.ipynb](/modules/02_llms_em_softwares/D_avaliacao_monitoramento/hands_on_evaluation.ipynb) |
