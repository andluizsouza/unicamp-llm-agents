# ADR 0001: Baseline stuffing com structured output

**Data:** 2026-09-07  
**Status:** aceito

## Contexto

O RecFair E1 precisa de um baseline honesto e testável para recomendação Top-5 por popularidade na janela de 7 dias, com abstenção e diversidade de marca (RF-07). O golden-set tem 30 casos (`golden_revision=cedba68fb6c4c54c`).

## Opções

1. **Stuffing** — catálogo + vendas no prompt; uma chamada Gemini com `json_schema`.
2. **Proxy SQL/heurística** — ranking determinístico sem LLM (não exercita interpretação de NL).
3. **RAG + tools no E1** — complexidade prematura sem limitação medida no baseline.

## Decisão

Adotar **(1) stuffing + structured output** (`architecture_id=baseline`, `prompt_version=v1`). Sem tools, memória, MCP ou LangGraph no E1.

## Consequências

- **Prós:** pipeline mínimo, contrato Pydantic estável, comparável nas evoluções E2–E4.
- **Contras:** ~28k chars de vendas no prompt; erros de agregação/janela pelo LLM; `e1_rate_restrict` 60% no run de referência (9/15).
- **Evidência E1:** `e1_rate_restrict` 9/15, `e1_rate_overall` 12/30, modelo `gemini-3.5-flash-lite`.

## Próximo incremento (E2, não implementado)

Text-to-SQL / tools para janela e preço; workflow LangGraph quando a limitação de stuffing for confirmada na comparação.
