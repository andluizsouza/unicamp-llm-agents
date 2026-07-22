# Seção B: LangGraph para Orquestração de Agentes Inteligentes

## TL;DR / Resumo Executivo
Esta seção apresenta o LangGraph como uma biblioteca para construir agentes inteligentes e workflows complexos com LLMs. Diferente de abordagens lineares, o LangGraph permite modelar fluxos com estado compartilhado, ciclos de reflexão, replanejamento e roteamento condicional, o que torna possível criar sistemas mais autônomos, robustos e fáceis de depurar.

## Conceitos Fundamentais (Tópicos Abordados)

- **LangGraph como framework de orquestração**: uso de grafos para representar a execução de agentes em vez de pipelines rígidos e lineares.
- **Estado compartilhado**: estrutura de dados persistente que funciona como memória de trabalho para o fluxo do agente.
- **Nós e arestas**: componentes do grafo que executam lógica e definem o encaminhamento entre etapas.
- **Reducers**: mecanismos para combinar atualizações do estado sem sobrescrever informações importantes.
- **Workflows agênticos**: padrões como pipeline, roteador, reflexivo e supervisor para resolver problemas com diferentes níveis de complexidade.
- **Loops e revisão**: suporte nativo a ciclos para reflexão, retry e replanejamento durante a execução.
- **Aplicação prática**: uso de notebooks para explorar a construção de fluxos e agentes com LangGraph.

## Matriz de Conteúdo: Aulas e Práticas da Seção B

| Aula | Tema Principal | Descrição Curta | Objetivo | Arquivo de Referência |
|------|----------------|----------------|----------|--------|
| 01 | Introdução ao LangGraph | Conceitos de grafo de execução, estado, nós, arestas, reducers e ciclos de execução para agentes inteligentes. | Apresentar o LangGraph como alternativa para arquiteturas mais dinâmicas e autônomas do que cadeias lineares. | [01_introducao.md](01_introducao.md) |
| 02 | Workflows e Orquestração Agêntica | Evolução de prompts para workflows, padrões de arquitetura e modelos de execução com loops e supervisão. | Mostrar como estruturar fluxos de trabalho mais complexos, com controle, modularidade e revisão. | [02_workflows.md](02_workflows.md) |
| Prática | LangGraph com Estado e Fluxo | Notebook introdutório com chatbot mínimo, uso de reducers, prompts de sistema, roteamento condicional e ciclo de geração-avaliação-revisão. | Explorar na prática os fundamentos de grafos, estado compartilhado e controle explícito do fluxo. | [hands_on_graph.ipynb](hands_on_graph.ipynb) |
| Prática | Workflows com LangGraph | Notebook voltado à construção de workflows agênticos, com padrões de orquestração e organização de etapas. | Aplicar os conceitos de workflow e orquestração em exemplos mais próximos de sistemas reais. | [hands_on_workflow.ipynb](hands_on_workflow.ipynb) |
