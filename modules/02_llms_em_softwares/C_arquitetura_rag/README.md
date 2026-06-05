# Bloco C: Arquitetura RAG

## TL;DR / Resumo Executivo
O Bloco C apresenta o **RAG (Retrieval-Augmented Generation)** como a arquitetura que conecta LLMs a conhecimento externo e atualizado, superando o limite do conhecimento estático dos modelos. Seu objetivo central é mostrar como projetar sistemas que recuperam trechos relevantes de bases documentais antes de gerar uma resposta, reduzindo alucinações, aumentando a rastreabilidade e melhorando a precisão em cenários corporativos e críticos. Ao final, o aluno compreende o pipeline completo de RAG — da ingestão de documentos ao uso em produção com estratégias de chunking, embeddings, retrieval e monitoramento.

## Conceitos Fundamentais (Tópicos Abordados)

- **RAG como Arquitetura**: Uso de recuperação de informação para fundamentar a geração do LLM com dados externos, privados e atualizáveis.
- **Componentes do Pipeline**: Retrievers, generators, embeddings, chunking e vector databases como peças centrais do fluxo de resposta.
- **Lost in the Middle**: Limitação de prompts longos e a perda de atenção em informações localizadas no meio do contexto.
- **Chunking e Embeddings**: Estratégias de segmentação de documentos e representação semântica para busca por similaridade.
- **Top-k, Re-ranking e RAG Híbrido**: Ajustes de recuperação para equilibrar precisão, ruído e latência.
- **Casos de Uso por Domínio**: Aplicações de RAG em contexto corporativo, jurídico, saúde, e-commerce, suporte técnico e educação.
- **Métricas e Monitoramento**: Indicadores de qualidade do sistema, latência, custo e feedback em produção.


## **Matriz de Conteúdo**: Aulas do Bloco C

| Aula | Tema Principal | Descrição Curta | Objetivo | Arquivo de Referência |
|------|----------------|----------------|----------|--------|
| 01 | Introdução ao RAG | Conceitos, arquitetura geral, problema do LLM isolado e fluxo de ingestão/inferência | Compreender por que o RAG é necessário e como ele conecta geração com conhecimento externo. | [01_intro_rag.md](/modules/02_llms_em_softwares/C_arquitetura_rag/01_intro_rag.md) |
| 02 | Arquiteturas RAG | Chunking, embeddings, métricas, top-k, re-ranking e variações de design | Aprender a ajustar o pipeline para melhorar recall, precisão e latência. | [02_arquitetura.md](/modules/02_llms_em_softwares/C_arquitetura_rag/02_arquitetura.md) |
| 03 | Casos de Uso de RAG | Aplicações por domínio, citação de fontes e monitoramento em produção | Avaliar como aplicar RAG em cenários reais com requisitos de rastreabilidade e controle. | [03_casos_uso.md](/modules/02_llms_em_softwares/C_arquitetura_rag/03_casos_uso.md) |
| Prática | Atividade em Notebook | Implementação de um pipeline RAG com LangChain e Groq | Aplicar o fluxo completo de RAG em ambiente de código, com busca semântica e geração contextualizada. | [hands_on_rag.ipynb](/modules/02_llms_em_softwares/C_arquitetura_rag/hands_on_rag.ipynb) |