# ADRs RecFair

Decisões arquiteturais datadas. Índice canônico — detalhes técnicos e diagramas em cada arquivo e no [mapa vigente](../architecture.md).

| Número | Título | Arquitetura | Data | Status |
| :---: | :--- | :--- | :--- | :--- |
| 0001 | [Baseline stuffing](0001-baseline.md) | `baseline` | 2026-09-07 | aceito |
| 0002 | [Workflow scoring determinístico](0002-workflow-scoring.md) | `workflow` | 2026-09-13 | aceito (executável) |
| 0003 | [Supervisor multiagente](0003-multiagent-supervisor.md) | `multiagent` | 2026-09-19 | aceito (vigente) |
| 0004 | [Régua nDCG@5 + RF + anti-inflação](0004-layered-evaluation-metrics.md) | eval | 2026-09-19 | aceito |
| 0005 | [Refinamento escopo transbordo](0005-handoff-scope-refinement.md) | `multiagent` | 2026-09-19 | aceito |

**Convenção:** nova peça (grafo, tool, MCP, memória, guardrail) → novo ADR numerado + atualizar `docs/architecture.md` no mesmo conjunto de mudanças. Mudança de critério de comparação → ADR próprio (0004), sem promover runtime.
