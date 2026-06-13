# Observabilidade e Monitoramento de LLMs em Produção

## TL;DR / Resumo Executivo
A transição de LLMs de notebooks para ambientes de produção exige que o desenvolvedor pare de avaliar o modelo isoladamente e passe a monitorar o sistema completo. A **observabilidade** é o conjunto de práticas que permite investigar cada etapa do pipeline (ingestão, recuperação, geração) para identificar e corrigir falhas silenciosas, como a degradação da qualidade, alucinações e aumentos inesperados de custo, garantindo a confiabilidade em escala real.

## Conceitos Fundamentais
*   **Observabilidade:** Capacidade de entender o estado interno de um sistema através dos dados que ele gera, permitindo investigar o que o usuário perguntou, qual prompt foi enviado, quais documentos foram recuperados e onde exatamente ocorreu uma falha.
*   **Logs:** Registros discretos de eventos individuais com *timestamp* (ex: prompt, resposta, ID do usuário) que descrevem "o que aconteceu".
*   **Métricas:** Valores numéricos agregados ao longo do tempo (ex: latência p95, custo por dia) que indicam a "frequência e intensidade" de eventos no sistema.
*   **Tracing:** Rastreio do fluxo completo de uma única requisição através de múltiplos componentes (retriever → LLM → resposta), indicando "onde no fluxo" algo ocorreu.
*   **Groundness:** Grau em que a resposta da IA está fundamentada exclusivamente no contexto recuperado, evitando alucinações baseadas em conhecimento prévio do modelo.
*   **Faithfulness:** Conceito similar ao groundness, focado na fidelidade da resposta em relação aos documentos fornecidos.
*   **NLI (Natural Language Inference):** Uso de modelos classificadores especialistas para detectar contradições entre a resposta gerada e o contexto.

## Matrizes de Comparação

### 1. Indicadores de Monitoramento (SLI e SLO)
| Indicador (SLI) | O que mede (Conceito) | SLO Típico (Meta) |
| :--- | :--- | :--- |
| **Latência p95** | Tempo de resposta para 95% das requisições. | < 3 segundos |
| **Throughput** | Volume de requisições processadas por segundo. | > 10 req/s |
| **Taxa de Erro** | Percentual de falhas técnicas sobre o total de requisições. | < 1% |
| **Custo / 1k req.** | Gasto financeiro médio em tokens por mil chamadas. | < $0.50 |
| **Groundedness** | Grau de fundamentação da resposta no contexto recuperado. | > 0.75 |
| **Precision@5** | Proporção de documentos úteis entre os 5 recuperados. | > 0.70 |
| **Satisfação** | Nível de aprovação declarado pelo usuário final. | > 80% |
| **Alucinação Rate** | Frequência de respostas inventadas ou sem sentido. | < 5% |

### 2. Avaliação Online pelo Usuário
| Sinal | Tipo | Interpretação |
| :--- | :--- | :--- |
| **Reformulação** | Implícito | A resposta anterior não foi útil para o usuário. |
| **Abandono** | Implícito | Frustração ou desinteresse do usuário com o sistema. |
| **Click em Fonte** | Implícito | O usuário sentiu necessidade de verificar a veracidade da informação. |
| **Thumbs Up/Down** | Explícito | Feedback direto; o *thumbs down* é o sinal mais valioso para correções. |
| **Escala Likert** | Explícito | Avaliação de 1 a 5 estrelas sobre a experiência. |

### 3. Tipos de Drifts em Sistemas de LLM
| Tipo de Drift | Definição | Exemplo Concreto |
| :--- | :--- | :--- |
| **Data Drift** | Mudança no perfil das perguntas dos usuários. | Perguntas de filosofia em um assistente de e-commerce. |
| **Concept Drift** | Mudança no significado de conceitos de negócio. | O critério do que é "urgente" muda internamente na empresa. |
| **Model Drift** | Atualização silenciosa do modelo pelo provedor. | Uma nova versão da API altera o estilo ou qualidade da resposta. |
| **Document Drift** | Mudança na indexação que altera os chunks. | A re-indexação prejudica o recall sem alterações no código. |

### 4. Checklist e Ferramentas em Produção
| Área | O que monitorar? | Ferramentas Comuns |
| :--- | :--- | :--- |
| **Modelo** | Qualidade (amostra LLM-as-a-judge), Custo total, Versão fixada. | **LangSmith:** Ideal para usuários de LangChain. |
| **RAG** | Precision@k, Groundedness, Contexto vazio. | **LangFuse:** Open source, foco em latência e precisão. |
| **Infra** | Latência p99, Throughput, Memória/GPU. | **Arize Phoenix:** Especializada em avaliação e RAG. |
| **Segurança** | Prompt Injection, Vazamento de PII, Tópicos proibidos. | **Helicone / W&B:** Monitoramento de experimentos e custo. |
| **Usuário** | Taxa de Thumbs Down, Reformulação, Tempo de sessão. | **OpenTelemetry:** Padrão aberto para tracing distribuído. |

## Diagrama de Fluxo Lógico (Pipeline e Erros em RAG)

O fluxo abaixo detalha onde falhas podem ocorrer no sistema e como elas são identificadas e corrigidas:

1.  **Usuário/Interface:** Erros de latência de rede (não-LLM).
2.  **Gerenciador de Prompts:** Erro em templates ou variáveis (Prompt frágil).
3.  **Retriever (Busca Vetorial):** 
    *   *Falha:* Documentos irrelevantes.
    *   *Identificação:* **Precision@k** baixo.
    *   *Correção:* Revisar embeddings e estratégias de *chunking*.
4.  **Re-ranker:** 
    *   *Falha:* Ordenação errada de documentos prioritários.
    *   *Correção:* Adicionar ou ajustar modelos de re-ranking.
5.  **Montagem do Contexto:** 
    *   *Falha:* Contexto excessivo (ruído) ou insuficiente (truncado).
    *   *Correção:* Ajustar o valor de **K**.
6.  **LLM Core:** 
    *   *Falha:* **Alucinação** (informação inventada).
    *   *Identificação:* Baixo **Groundedness** via NLI ou LLM-as-a-judge.
    *   *Correção:* Melhorar o prompt ou o contexto fornecido.
7.  **Pós-processamento:** 
    *   *Falha:* Erros de parsing, validação de JSON ou formatação final.