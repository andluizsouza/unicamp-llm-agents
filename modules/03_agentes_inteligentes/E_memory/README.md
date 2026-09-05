# Seção E: Memória em Agentes Inteligentes

## TL;DR / Resumo Executivo
Esta seção descreve os princípios e práticas para projetar subsistemas de memória que permitem a operação de agentes baseados em LLMs em tarefas de longo horizonte. Cobre tipos de memória (curto prazo, semântica, episódica e procedural), ciclo de vida (escrita, recuperação, atualização, esquecimento) e padrões avançados como Memória Reflexiva e compressão de histórico.

## Conceitos Fundamentais (Tópicos Abordados)

- **Natureza stateless dos LLMs:** por que precisamos de memória externa e quais problemas ela resolve.
- **Janela de Contexto vs. Memória Externa:** trade-offs de custo, persistência e capacidade.
- **Tipos de Memória:** curto prazo (workbench/state), semântica (fatos), episódica (experiências) e procedural (regras e skills).
- **Ciclo de Vida da Memória:** escrita seletiva, indexação por similaridade, atualização e mecanismos de esquecimento.
- **Memória Reflexiva:** aprendizado não-paramétrico via autorreflexão e reforço verbal.
- **Compressão e gerenciamento de contexto:** truncamento, janela deslizante e sumarização para sessões longas.

## Matriz de Conteúdo

| Aula | Tema Principal | Descrição Curta | Objetivo | Arquivo de Referência |
|------|----------------|----------------|----------|--------|
| 01 | Memória em Agentes LLMs | Fundamentos sobre por que e como arquitetar memória externa para agentes. | Explicar tipos de memória e ciclo de vida. | [1_memoria_agentes.md](/modules/03_agentes_inteligentes/E_memory/1_memoria_agentes.md) |
| 02 | Memória Reflexiva | Arquiteturas de autorreflexão e reforço verbal para aprendizado contínuo. | Mostrar como capturar lições e melhorar decisões sem retreino. | [2_memoria_reflexiva.md](/modules/03_agentes_inteligentes/E_memory/2_memoria_reflexiva.md) |
| Prática | Memória em Ação | Exercícios para implementar escrita, busca semântica e políticas de retenção. | Familiarizar o aluno com pipelines RAG e gerenciamento de sessão. | Notebooks práticos: [hands_on_memory.ipynb](/modules/03_agentes_inteligentes/E_memory/hands_on_memory.ipynb) [hands_on_memory_2.ipynb](/modules/03_agentes_inteligentes/E_memory/hands_on_memory_2.ipynb) |