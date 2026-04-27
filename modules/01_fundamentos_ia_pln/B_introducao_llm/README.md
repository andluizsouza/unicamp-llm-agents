# Bloco B: Introdução aos Grandes Modelos de Linguagem (LLMs)

## TL;DR / Resumo Executivo
O Bloco B aprofunda os fundamentos técnicos que tornaram possíveis os Grandes Modelos de Linguagem modernos. Seu objetivo central é apresentar os três pilares da arquitetura das LLMs: o **mecanismo de autoatenção (self-attention)** dos Transformers, o processo de **tokenização e embeddings** que converte linguagem em matemática, e a **arquitetura interna Decoder-Only** que sustenta modelos como GPT, Gemini e Llama. Ao fim, o aluno terá compreensão sólida do fluxo completo — do prompt do usuário até a geração token a token.

## Conceitos Fundamentais (Tópicos Abordados)

- **Mecanismos de Atenção**: Funcionamento do Scaled Dot-Product Attention com vetores Query (Q), Key (K) e Value (V), e como o Multi-Head Attention captura múltiplas relações contextuais em paralelo.
- **Arquiteturas Encoder-Decoder vs. Decoder-Only**: Diferenças estruturais, casos de uso ideais e por que a abordagem Decoder-Only tornou-se o padrão para LLMs generativas.
- **Tokenização**: Metodologias de quebra de texto em unidades processáveis, desde Word Tokens clássicos até o estado da arte com BPE (*Byte-Pair Encoding*).
- **Embeddings Estáticos e Dinâmicos**: Como vetores numéricos representam o significado das palavras e como embeddings contextuais (gerados por camadas de atenção) resolvem ambiguidades semânticas.
- **Geração Autorregressiva**: O loop de predição token a token, com o papel do LM Head, Logits, Softmax e parâmetros como Temperature.
- **Otimizações de Escalabilidade**: Técnicas como **KV-cache** (evita reprocessamento), **RoPE** (posicionamento relativo para contextos longos) e **MoE** (*Mixture of Experts* para eficiência computacional).


## **Matriz de Conteúdo**: Aulas do Bloco B

| Aula | Tema Principal | Descrição Curta | Objetivo | Arquivo de Referência |
|------|----------------|----------------|----------|--------|
| 01 | Mecanismos de Atenção e Transformers | Autoatenção, Q/K/V, Multi-Head Attention e arquiteturas Encoder-Decoder vs. Decoder-Only | Compreender o mecanismo central que substituiu RNNs e viabilizou as LLMs modernas. | [01_attention_transformers.md](/modules/01_fundamentos_ia_pln/B_introducao_llm/01_attention_transformers.md) |
| 02 | Tokens e Embeddings | Tokenização (BPE, WordPiece), Token IDs e embeddings estáticos vs. dinâmicos | Entender como texto é convertido em representações numéricas processáveis pelos Transformers. | [02_tokens_embeddings.md](/modules/01_fundamentos_ia_pln/B_introducao_llm/02_tokens_embeddings.md) |
| 03 | Arquiteturas e Funcionamento dos LLMs | Geração autorregressiva, LM Head, KV-cache, RoPE e MoE | Detalhar o funcionamento interno e as otimizações das arquiteturas modernas de LLMs. | [03_arquitetura_llm.md](/modules/01_fundamentos_ia_pln/B_introducao_llm/03_arquitetura_llm.md) |
| Prática | Atividade em Notebook | Tokenização e geração com Transformers usando o modelo Mistral-7B | Aplicar os conceitos de tokenização, pipelines e parâmetros de geração em ambiente de código. | [hands_on_tokens_embeddings.ipynb](/modules/01_fundamentos_ia_pln/B_introducao_llm/hands_on_tokens_embeddings.ipynb) |
