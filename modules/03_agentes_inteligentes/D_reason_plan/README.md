# Seção D: Reasoning, Planning e Deep Agents

## TL;DR / Resumo Executivo
Esta seção reúne os conceitos fundamentais que permitem transformar um LLM em um agente mais robusto, capaz de pensar de forma estruturada, planejar sequências de ação e operar em tarefas de longo horizonte. O foco é mostrar como o agente passa de uma resposta imediata para um processo organizado de raciocínio, execução e adaptação.

## Conceitos Fundamentais (Tópicos Abordados)

- **Reasoning (Raciocínio)**: como o agente constrói conclusões, compara alternativas e torna o processo de decisão mais visível e auditável.
- **Planning (Planejamento)**: como decompor objetivos complexos em passos organizados, respeitando dependências e permitindo replanejamento.
- **Deep Agents**: como escalar agentes para tarefas longas, com memória externa, gerenciamento de contexto e delegação para subagentes.
- **Prática aplicada**: notebooks que ilustram, de forma didática, como implementar e comparar essas abordagens em exemplos reais.

## Matriz de Conteúdo

| Aula | Tema Principal | Descrição Curta | Objetivo | Arquivo de Referência |
|------|----------------|----------------|----------|--------|
| 01 | Raciocínio em Agentes LLMs | Introdução às técnicas de reasoning, como Few-Shot, Chain-of-Thought, Self-Ask, Self-Consistency, ReAct, Least-to-Most e Tree of Thoughts. | Mostrar como tornar o raciocínio do agente mais explícito, auditável e útil para tomada de decisão. | [01_reasoning.md](01_reasoning.md) |
| 02 | Planejamento em Agentes LLMs | Exploração de estratégias de planejamento, como ReAct, Plan-and-Execute, ReWOO, Reflection e Tree of Thoughts. | Ensinar como transformar objetivos complexos em planos acionáveis e adaptáveis. | [02_planning.md](02_planning.md) |
| 03 | Deep Agents | Apresentação de arquiteturas para tarefas de longo horizonte, com planejamento explícito, offloading de contexto e subagentes. | Demonstrar como sustentar agentes em fluxos extensos e processos que ultrapassam a janela de contexto. | [03_deep_agents.md](03_deep_agents.md) |
| Prática | Reasoning em Ação | Notebook com exemplos práticos das técnicas de reasoning e da exposição do raciocínio. | Familiarizar o aluno com a implementação e comparação de diferentes abordagens de raciocínio. | [hands_on_reasoning.ipynb](hands_on_reasoning.ipynb) |
| Prática | Planning em Ação | Notebook com implementação de estratégias de planejamento em grafos e agentes. | Mostrar como estruturar planos, executar etapas e replanejar quando necessário. | [hands_on_planning.ipynb](hands_on_planning.ipynb) |
| Prática | Deep Agents em Ação | Notebook com a construção de componentes de deep agents e comparação com agentes rasos. | Explorar a gestão de contexto, memória externa e delegação em tarefas mais longas. | [hands_on_DeepAgents.ipynb](hands_on_DeepAgents.ipynb) |