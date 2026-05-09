# Bloco C: Uso e Ajuste Fino de LLMs

## TL;DR / Resumo Executivo
O Bloco C fecha o ciclo prático do módulo, mostrando como transformar um modelo de linguagem generalista em uma ferramenta especializada e alinhada a valores humanos. Seu objetivo central é apresentar as estratégias de **reaproveitamento de modelos pré-treinados** para tarefas como classificação e modelagem de tópicos, e detalhar o pipeline completo de ajuste fino — do **SFT (Supervised Fine-Tuning)** ao **alinhamento de preferências (DPO/RLHF)** — com técnicas eficientes como **LoRA** e **QLoRA** que viabilizam o treinamento em hardware comum.

## Conceitos Fundamentais (Tópicos Abordados)

- **Reaproveitamento de Modelos Pré-treinados**: Uso de LLMs como classificadores diretos (task-specific) ou como extratores de embeddings para alimentar classificadores de ML tradicionais.
- **Análise de Sentimento e Classificação de Texto**: Aplicação prática de modelos como RoBERTa e embeddings + Regressão Logística para categorização automática de documentos.
- **Modelagem de Tópicos (BERTopic)**: Pipeline de quatro etapas — geração de embeddings, redução de dimensionalidade (UMAP), clusterização (HDBSCAN) e representação (c-TF-IDF) — para descoberta de temas em grandes volumes de texto.
- **Pré-treinamento e SFT**: A transição do modelo base (foundation model) para um assistente capaz de seguir instruções por meio de ajuste fino supervisionado com pares instrução/resposta.
- **PEFT, LoRA e QLoRA**: Técnicas de ajuste fino eficiente que congelam a maior parte dos pesos originais, reduzindo em até 99,8% os parâmetros treináveis e permitindo o treinamento de modelos imensos com hardware comum.
- **Ajuste de Preferência — RLHF e DPO**: Etapa final de alinhamento que ensina o modelo a priorizar respostas úteis, seguras e éticas a partir de comparações entre respostas "vencedoras" e "perdedoras".
- **Pipeline Prático de Fine-tuning**: Formatação de prompts com templates de chat, treinamento por predição do próximo token, merge de adapters LoRA e avaliação do modelo resultante.


## **Matriz de Conteúdo**: Aulas do Bloco C

| Aula | Tema Principal | Descrição Curta | Objetivo | Arquivo de Referência |
|------|----------------|----------------|----------|--------|
| 01 | Uso de Modelos Pré-treinados | Classificação de texto, análise de sentimento e modelagem de tópicos com LLMs | Explorar estratégias de reaproveitamento de modelos pré-treinados sem necessidade de retreinamento completo. | [01_uso_modelo_pre_treinado.md](/modules/01_fundamentos_ia_pln/C_uso_ajuste_llm/01_uso_modelo_pre_treinado.md) |
| 02 | Conceitos de Fine-tuning | Pré-treinamento, SFT, LoRA, QLoRA, RLHF e DPO | Compreender o fluxo de refinamento de LLMs e as técnicas eficientes de ajuste fino. | [02_conceitos_finetune.md](/modules/01_fundamentos_ia_pln/C_uso_ajuste_llm/02_conceitos_finetune.md) |
| 03 | Prática de Fine-tuning | Pipelines de SFT e DPO com QLoRA aplicados a modelos reais | Detalhar a implementação prática do ajuste fino supervisionado e por preferência com eficiência computacional. | [03_pratica_finetune.md](/modules/01_fundamentos_ia_pln/C_uso_ajuste_llm/03_pratica_finetune.md) |
| Prática | Preparação de Dataset | Coleta, limpeza e formatação de dados para fine-tuning | Aplicar os conceitos de curadoria de dados em ambiente de código. | [hands_on_dataset.ipynb](/modules/01_fundamentos_ia_pln/C_uso_ajuste_llm/hands_on_dataset.ipynb) |
| Prática | Fine-tuning v1 | Ajuste fino supervisionado (SFT) com QLoRA | Executar um pipeline completo de SFT em ambiente de código. | [hands_on_finetune_v1.ipynb](/modules/01_fundamentos_ia_pln/C_uso_ajuste_llm/hands_on_finetune_v1.ipynb) |
| Prática | Fine-tuning v2 | Ajuste de preferência (DPO) e avaliação do modelo final | Aplicar DPO sobre o modelo SFT e comparar os resultados em ambiente de código. | [hands_on_finetune_v2.ipynb](/modules/01_fundamentos_ia_pln/C_uso_ajuste_llm/hands_on_finetune_v2.ipynb) |
