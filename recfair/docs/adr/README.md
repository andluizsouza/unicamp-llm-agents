# ADRs RecFair

Decisões arquiteturais datadas. Índice canônico — detalhes técnicos e diagramas em cada arquivo e no [mapa vigente](../architecture.md).

| Número | Título | Arquitetura | Data | Status |
| :---: | :--- | :--- | :--- | :--- |
| 0001 | [Baseline stuffing](0001-baseline.md) | `baseline` | 2026-09-07 | aceito |
| 0002 | [Workflow scoring determinístico](0002-workflow-scoring.md) | `workflow` | 2026-09-13 | aceito (executável) |
| 0003 | [RecFair E3 — multiagente, régua e roteamento](0003-multiagent-supervisor.md) | `multiagent` + `eval/` | 2026-09-19 | aceito (executável) |
| 0004 | [RecFair E4 — harness resiliente e avaliação ética](0004-resilient-harness.md) | `resilient` + `eval/` | 2026-09-27 | aceito (vigente) |

**Convenção:** nova peça (grafo, tool, MCP, memória, guardrail, harness) → novo ADR numerado + atualizar `docs/architecture.md` no mesmo conjunto de mudanças. O entregável E4 (resiliência e ética) está documentado no ADR 0004.
