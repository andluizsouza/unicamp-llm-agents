---
name: architecture-adrs
description: >-
  Escreve e atualiza ADRs datados e o mapa de arquitetura de sistemas
  multiagente. Use ao escolher modelo, storage, MCP vs tool local, padrão de
  grafo, critério de promoção, ou qualquer decisão que altere custo, risco ou
  complexidade.
---

# ADRs e arquitetura

## Quando gravar ADR

Obrigatório se a mudança:

- introduz ou remove uma peça (tools, RAG, MCP, grafo, agente, memória);
- troca LLM, embeddings, vector store ou provedor MCP;
- altera o golden-set (acréscimo ou correção de defeito) ou o critério de comparação;
- muda human-in-the-loop.

Não grave ADR para typo, rename local ou dependência de lint.

Cada arquitetura tem data (ISO) no ADR e no mapa. A versão do incremento vigente fica no runtime (default do CLI) mesmo se o eval empatar ou piorar — o ADR registra o resultado. Peças **extras** sem evidência: não implementar.

## Arquivos

```
docs/architecture.md      # estado atual + data da última promoção
docs/adr/NNNN-slug.md     # decisões
docs/adr/README.md        # índice: número, título, data, status
```

Template: [adr-template.md](adr-template.md). Numeração `0001`, `0002`, … sem buracos. Status: proposto | aceito | rejeitado | substituído | depreciado.

## Conteúdo mínimo

1. **Data** — obrigatória.
2. **Contexto** — limitação medida (cite `run_id` / resultado de eval) ou restrição explícita.
3. **Opções** — pelo menos duas reais, incluindo “ficar como está”.
4. **Decisão** — o que entra, o que fica fora.
5. **Consequências** — complexidade, custo, latência, o que o eval passa a cobrir.
6. **Evidência** — ganho, empate ou piora (mesmo modelo, baseline reexecutado) + hipótese. Empate/piora não apagam o incremento vigente.

Rejeite ADR cuja justificativa seja “é mais profissional” ou “vamos precisar depois”, salvo se a entrega **exige** aquela peça — aí a justificativa é a limitação do baseline que a peça ataca.

## architecture.md

Atualize no mesmo conjunto de mudanças da promoção. Deve responder:

- Arquitetura vigente (default do CLI): `id`, **data**, peças ligadas.
- Diagrama mermaid do fluxo **que existe no código**.
- Como executar: `make chat` / `make eval` / `ARCH=baseline`.
- Contratos de entrada/saída (estáveis entre versões).
- Hard-stops e human-in-the-loop.
- O que deliberadamente **não** está no sistema.
- Histórico (id, data, ADR) das versões ainda executáveis.

Não descreva um supervisor se o código ainda é um prompt.
