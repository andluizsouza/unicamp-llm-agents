# ADR 0002: Workflow determinístico com scoring por pontos

**Data:** 2026-09-13  
**Status:** aceito

## Contexto

O baseline E1 (stuffing) falha em agregação determinística, promo/estoque/preço e memória multi-turn. O E2 precisa de fluxo explícito, tools reais sobre SQLite, memória de sessão e régua de gabarito unificada para comparar baseline reexecutado vs `workflow`.

## Opções

1. **ReAct híbrido** — LLM decide cada passo de scoring (alto custo, não determinístico).
2. **Workflow determinístico** — LLM só em `parse_intent`; pipeline de 7 passos fixo via `scoring/engine.py`.
3. **Proxy SQL sem LLM** — não interpreta NL nas entradas do golden-set.

## Decisão

Adotar **(2) workflow LangGraph** (`architecture_id=workflow`, `prompt_version=v2`):

- `parse_intent` (Gemini) → roteamento abstain vs scoring.
- Nós fixos delegam a `scoring/engine.py` (fonte única de gabarito em `eval/gold.py`).
- `MemorySaver` + `thread_id` para T31–T33.
- Tools locais SQLite (`tb_catalogo`, `tb_vendas`, `tb_claims`, `tb_inventory`); sem MCP no E2.
- `ScoreTrace` por passo; CLI `/trace` e `/reset`.

### Dados novos

- `tb_claims`: 40 SKUs × 5 `claim_type`, texto curado de PDPs públicas [boticario.com.br](https://www.boticario.com.br/); rastreio em `data/claims_manifest.json` (`source_url`, `captured_at=2026-09-13`).
- `tb_inventory`: snapshot `2026-09-01`; `E4N8J1` estoque 0; `G7Q2D4` launch; `3G7P2W` promo.

### Golden-set

- T01–T30 entradas imutáveis; gabarito recalculado via engine quando a régua scoring diverge do E1.
- Novos T31–T38: memória (T31–T33) e dimensões de scoring (T34–T38).

## Consequências

- **Prós:** determinismo offline = runtime; baseline comparável na mesma régua; observabilidade por passo; memória isolada por `thread_id`.
- **Contras:** dependência LangGraph; `parse_intent` ainda sujeito a erro de NL; guardrails PII/injection (T26–T30) permanecem gap documentado (E3+).
- **Métricas E2:** `e2_rate_restrict`, `e2_rate_scoring`, `e2_rate_memory`, `e2_rate_overall` no runner/report.

## Próximo incremento (E3, não implementado)

Guardrails PII (`sanitize_pii`) e auditoria de fairness; MCP opcional se integração externa for medida.
