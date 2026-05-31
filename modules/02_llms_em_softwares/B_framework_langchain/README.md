# Bloco B: Framework LangChain

## TL;DR / Resumo Executivo
O Bloco B apresenta o **LangChain** como framework de orquestração para construção de sistemas de software robustos baseados em LLMs. Seu objetivo central é capacitar o desenvolvedor a ir além de chamadas isoladas de API, dominando a integração de modelos com **ferramentas externas**, **bancos vetoriais** e **memória conversacional**, e a construção de **pipelines modulares** com a linguagem declarativa LCEL — incluindo topologias sequenciais, paralelas e condicionais, estratégias de fallback e padrões como RAG (Retrieval-Augmented Generation) para sistemas de produção.

## Conceitos Fundamentais (Tópicos Abordados)

- **LangChain como Orquestrador**: Coordenação de LLMs, ferramentas, memória e agentes em um framework modular com mais de 700 integrações disponíveis.
- **LCEL (LangChain Expression Language)**: Linguagem declarativa com operador pipe (`|`) para composição de cadeias modulares e legíveis, baseada na interface unificada Runnable.
- **Integrações e Portabilidade**: Alternância entre provedores (OpenAI, Groq, Hugging Face) com mudanças mínimas no código via interface padronizada `invoke()`.
- **RAG (Retrieval-Augmented Generation)**: Pipeline completo de ingestão, vetorização, armazenamento e recuperação de documentos para enriquecer o contexto do modelo com dados privados.
- **Bancos Vetoriais**: Armazenamento e busca por similaridade semântica com tecnologias como FAISS, Chroma e Pinecone.
- **Memória Conversacional**: Estratégias de persistência de estado (Buffer, Window, Summary) para manter contexto entre interações.
- **Agentes e Ciclo ReAct**: Sistemas que utilizam o LLM como raciocinador para decidir dinamicamente quais ferramentas chamar (Reasoning and Acting).
- **Pipelines Modulares**: Topologias sequencial, paralela e condicional com Output Parsers, fallbacks e tratamento de erros para produção.


## **Matriz de Conteúdo**: Aulas do Bloco B

| Aula | Tema Principal | Descrição Curta | Objetivo | Arquivo de Referência |
|------|----------------|----------------|----------|--------|
| 01 | Introdução ao LangChain | Conceitos de Chains, Tools, Memory, Agents, LCEL e ciclo ReAct | Compreender o papel do LangChain como orquestrador e seus componentes fundamentais. | [01_intro_langchain.md](/modules/02_llms_em_softwares/B_framework_langchain/01_intro_langchain.md) |
| 02 | Integrações e Conectividade | Provedores de LLM, Document Loaders, Embeddings, Vector Stores e Tools | Dominar a integração de LLMs com fontes de dados externas e bancos vetoriais para construção de sistemas RAG. | [02_integracoes.md](/modules/02_llms_em_softwares/B_framework_langchain/02_integracoes.md) |
| 03 | Construção de Pipelines | LCEL, topologias de pipeline, Output Parsers, fallbacks e boas práticas de produção | Construir pipelines robustos e modulares com roteamento, tratamento de erros e escalabilidade. | [03_pipelines.md](/modules/02_llms_em_softwares/B_framework_langchain/03_pipelines.md) |
| Prática | Atividade em Notebook | Implementação de chains, integrações e pipelines com LangChain | Aplicar os conceitos de orquestração, RAG e pipelines em ambiente de código. | [hands_on_langchain.ipynb](/modules/02_llms_em_softwares/B_framework_langchain/hands_on_langchain.ipynb) |
