# Avaliação de Sistemas com Large Language Models (LLMs)

## TL;DR / Resumo Executivo
O objetivo central deste bloco é compreender que a avaliação de LLMs não é universal, mas **dependente do contexto** (ex: precisão no ramo jurídico vs. naturalidade em chatbots). Avaliar sistemas de IA envolve equilibrar a qualidade das respostas (fidelidade, clareza, factualidade) com métricas de engenharia como **custo, latência (P95) e throughput**, permitindo decisões fundamentadas entre o uso de APIs proprietárias ou modelos locais quantizados.

## Conceitos Fundamentais
*   **LLM-as-a-Judge (LLM Juiz):** Técnica onde um modelo de linguagem mais capaz (ex: GPT-4o) analisa e pontua as respostas produzidas por outro modelo.
*   **Latência P95:** Métrica de performance que indica o tempo máximo em que 95% das requisições foram processadas, sendo essencial para medir a experiência do usuário.
*   **Escala Likert:** Escala de pontuação (geralmente de 1 a 5) utilizada por avaliadores humanos ou LLMs para julgar critérios como clareza e utilidade.
*   **Quantização:** Processo de reduzir a precisão dos pesos de um modelo (ex: de 32 bits para 4 bits) para diminuir o consumo de memória (VRAM) e permitir a execução em hardware local.
*   **Métricas Textuais Clássicas:** Algoritmos (BLEU, ROUGE) que comparam a sobreposição de palavras entre uma resposta gerada e uma referência "padrão ouro".
*   **Similaridade Semântica (BERTScore):** Avaliação baseada em modelos de linguagem (como BERT) que identifica se duas frases têm o mesmo significado, mesmo usando palavras diferentes.

## Matriz de Comparação

### 1. Metodologias de Avaliação de Qualidade

| Metodologia | Definição | Quando Usar | Pontos Positivos | Pontos Negativos |
| :--- | :--- | :--- | :--- | :--- |
| **Humana** | Especialistas revisam e pontuam as respostas. | Casos críticos (saúde/jurídico) e validação final. | Alta validade e percepção de nuances humanas. | Cara, lenta, não escalável e sujeita a fadiga. |
| **Métricas Textuais (BLEU/ROUGE)** | Comparação matemática de palavras exatas. | Tradução (BLEU) e sumarização (ROUGE). | Rápidas, baratas e objetivas. | Ignoram semântica e sinônimos; penalizam criatividade. |
| **LLM-as-a-Judge** | Um LLM atua como juiz imparcial. | Avaliação em larga escala e pipelines de automação. | Escalável, consistente e rápida. | Pode ter vieses (prefere respostas longas) e instabilidade. |

### 2. Infraestrutura: API vs. Modelo Local

| Categoria | Quando Usar | Exemplos | Pontos Positivos | Pontos Negativos |
| :--- | :--- | :--- | :--- | :--- |
| **API Proprietária** | Prototipagem rápida e baixo volume de requisições. | GPT-4o, Gemini, Claude. | Facilidade de uso e escalabilidade imediata. | Custo por token e menor privacidade de dados sensíveis. |
| **Modelo Local** | Volume massivo (>1M req/mês) ou dados ultra sensíveis. | Llama 3.1, Mistral (via Olhama). | Privacidade total e sem custo variável por token. | Exige hardware caro (GPUs) e manutenção técnica. |

## Diagrama de Fluxo Lógico (Pipeline de Avaliação)

O processo para avaliar e escolher o melhor sistema de LLM segue este fluxo linear e iterativo:

1.  **Definição da Tarefa:** Identificar o foco principal (ex: precisão jurídica vs. naturalidade de chat).
2.  **Criação do Dataset de Teste:** Selecionar de 50 a 100 exemplos representativos, incluindo casos de borda (*edge cases*) para maior robustez.
3.  **Execução do Modelo:** Gerar as respostas para o subconjunto de testes utilizando os modelos candidatos.
4.  **Coleta de Métricas Técnicas:** Medir o custo estimado por token e a latência P95 das requisições.
5.  **Aplicação da Avaliação de Qualidade:**
    *   Usar **Métricas Textuais** para triagem rápida.
    *   Usar **LLM-as-a-Judge** (com temperatura 0 e justificativa) para escala.
    *   Usar **Avaliação Humana** em uma amostra (0,1%) para validar o juiz automatizado.
6.  **Análise de Correlação:** Verificar via Coeficiente de Kappa se as notas do LLM Juiz são parecidas com as dos humanos.
7.  **Decisão Final e Iteração:** Selecionar o modelo com melhor custo-benefício e refinar os prompts conforme os erros encontrados.