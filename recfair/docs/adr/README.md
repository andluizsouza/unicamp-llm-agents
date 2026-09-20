# ADRs RecFair

Decisões arquiteturais datadas. Índice canônico — detalhes técnicos e diagramas em cada arquivo e no [mapa vigente](../architecture.md).

| Número | Título | Arquitetura | Data | Status |
| :---: | :--- | :--- | :--- | :--- |
| 0001 | [Baseline stuffing](0001-baseline.md) | `baseline` | 2026-09-07 | aceito |
| 0002 | [Workflow scoring determinístico](0002-workflow-scoring.md) | `workflow` | 2026-09-13 | aceito (executável) |
| 0003 | [RecFair E3 — multiagente, régua e roteamento](0003-multiagent-supervisor.md) | `multiagent` + `eval/` | 2026-09-19 | aceito (vigente) |

**Convenção:** nova peça (grafo, tool, MCP, memória, guardrail) → novo ADR numerado + atualizar `docs/architecture.md` no mesmo conjunto de mudanças. O entregável E3 (runtime, régua e roteamento) está documentado integralmente no ADR 0003.
