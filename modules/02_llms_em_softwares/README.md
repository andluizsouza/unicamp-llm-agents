# Módulo 02: LLMs em Softwares

## TL;DR / Resumo Executivo
O Módulo 02 leva do uso isolado de LLMs para a construção de sistemas de software robustos e aplicáveis. Partindo da engenharia de prompts e configuração de modelos via API, o módulo avança para a orquestração com LangChain, a arquitetura RAG para conectar modelos a conhecimento externo e, por fim, a avaliação e monitoramento para garantir qualidade, custo e confiabilidade em produção. O objetivo final é apresentar ferramentas para projetar, implementar e operar aplicações baseadas em LLMs com foco em software real.

## Estrutura do Módulo

```
02_llms_em_softwares/
├── A_llms_prompts/            # Bloco A — LLMs e Engenharia de Prompts
├── B_framework_langchain/     # Bloco B — Framework LangChain
├── C_arquitetura_rag/         # Bloco C — Arquitetura RAG
├── D_avaliacao_monitoramento/ # Bloco D — Avaliação e Monitoramento
└── hands_on_final_test.ipynb  # Avaliação final integradora
```

## Índice de Blocos

| Bloco | Tema | Descrição | README |
|-------|------|-----------|--------|
| **A** | LLMs e Engenharia de Prompts | Integração de modelos via API, hiperparâmetros de geração, prompts estruturados, few-shot, Chain-of-Thought e orquestração de inferência. | [A_llms_prompts/README.md](/modules/02_llms_em_softwares/A_llms_prompts/README.md) |
| **B** | Framework LangChain | Orquestração de LLMs com ferramentas, memória, bancos vetoriais, pipelines modulares e LCEL. | [B_framework_langchain/README.md](/modules/02_llms_em_softwares/B_framework_langchain/README.md) |
| **C** | Arquitetura RAG | Recuperação de conhecimento externo para fundamentar respostas, com chunking, embeddings, retrieval e estratégias para produção. | [C_arquitetura_rag/README.md](/modules/02_llms_em_softwares/C_arquitetura_rag/README.md) |
| **D** | Avaliação e Monitoramento | Métricas de qualidade, LLM-as-a-Judge, groundedness, custo, latência e observabilidade em produção. | [D_avaliacao_monitoramento/README.md](/modules/02_llms_em_softwares/D_avaliacao_monitoramento/README.md) |
| | Teste Final | Avaliação integradora cobrindo conceitos dos Blocos A, B, C e D | [hands_on_final_test.ipynb](/modules/02_llms_em_softwares/hands_on_final_test.ipynb) |
