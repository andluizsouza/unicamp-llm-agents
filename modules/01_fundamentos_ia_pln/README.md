# Módulo 01: Fundamentos de IA e Processamento de Linguagem Natural

## TL;DR / Resumo Executivo
O Módulo 01 constrói o alicerce teórico e prático necessário para compreender os Grandes Modelos de Linguagem (LLMs). Partindo da evolução histórica da Inteligência Artificial e dos fundamentos de Machine Learning e Deep Learning, o módulo avança para os mecanismos internos dos Transformers — autoatenção, tokenização e embeddings — e culmina nas técnicas de ajuste fino (Fine-tuning) que permitem transformar modelos generalistas em ferramentas especializadas. Ao final, o aluno terá domínio completo do ciclo: da teoria fundacional até a prática de SFT e DPO com LoRA/QLoRA.

## Estrutura do Módulo

```
01_fundamentos_ia_pln/
├── A_fundamentos_ia/          # Bloco A — Fundamentos da IA
├── B_introducao_llm/          # Bloco B — Introdução aos LLMs
├── C_uso_ajuste_llm/          # Bloco C — Uso e Ajuste Fino
└── hands_on_final_test.ipynb  # Avaliação final integradora
```

## Índice de Blocos

| Bloco | Tema | Descrição | README |
|-------|------|-----------|--------|
| **A** | Fundamentos da Inteligência Artificial | Evolução histórica da IA, paradigmas de Machine Learning (supervisionado, não supervisionado, auto-supervisionado), Redes Neurais (MLP, CNN, RNN) e Transfer Learning. | [A_fundamentos_ia/README.md](/modules/01_fundamentos_ia_pln/A_fundamentos_ia/README.md) |
| **B** | Introdução aos Grandes Modelos de Linguagem | Mecanismos de atenção e Transformers, tokenização (BPE), embeddings estáticos e dinâmicos, arquitetura Decoder-Only e geração autorregressiva com otimizações (KV-cache, RoPE, MoE). | [B_introducao_llm/README.md](/modules/01_fundamentos_ia_pln/B_introducao_llm/README.md) |
| **C** | Uso e Ajuste Fino de LLMs | Reaproveitamento de modelos pré-treinados, classificação de texto, modelagem de tópicos (BERTopic), pipeline completo de Fine-tuning com SFT, LoRA/QLoRA e alinhamento por RLHF/DPO. | [C_uso_ajuste_llm/README.md](/modules/01_fundamentos_ia_pln/C_uso_ajuste_llm/README.md) |
| | Teste Final | Avaliação integradora cobrindo conceitos dos Blocos A, B e C | [hands_on_final_test.ipynb](/modules/01_fundamentos_ia_pln/hands_on_final_test.ipynb) |
