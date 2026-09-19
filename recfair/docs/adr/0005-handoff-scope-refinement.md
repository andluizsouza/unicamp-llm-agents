# ADR 0005: Refinamento do escopo de transbordo

- Status: aceito
- Data: 2026-09-19
- Arquitetura: `multiagent` (emenda ao ADR 0003)
- Autores: RecFair E3

## Contexto

O ADR 0003 tratava **fora de domínio** e **transbordo humano in-contexto** como o mesmo destino `handoff`, sempre com telefone `0800-000-0000`. Isso gerava transbordo indevido para perguntas totalmente externas a O Boticário (imposto de renda, clima, jurídico geral).

O produto exige dois comportamentos distintos:

1. **Fora de contexto** — template fixo simpático explicando a função do assistente, **sem** telefone.
2. **Transbordo humano** — perguntas sobre o negócio Boticário que não são ranking nem FAQ respondível pela KB.

Casos golden T43, T57 e T58 mediam transbordo quando deveriam medir redirecionamento (defeito real de régua, corrigido neste incremento).

## Opções

### A — Reutilizar `abstention` com novo `reason`

Prós: sem novo status. Contras: mistura abstenção de catálogo (fluxo recommendation) com recusa de escopo; confunde Painel A e H.4.

### B — Novo domínio `out_of_context` + nó determinístico (escolhida)

Prós: contrato explícito; verificação separada (`G_out_of_context`); handoff reservado a in-contexto. Contras: +1 aresta no grafo; golden T43/T57/T58 reclassificados.

### C — Manter handoff único com template condicional

Prós: diff mínimo. Contras: `RecFairOutput` não distingue telefone vs não-telefone de forma estável; eval frágil.

## Decisão

Escolhemos **B**:

- `Domain` e `RecFairOutput.status` ganham `out_of_context`.
- Nó `out_of_context_node` emite `OUT_OF_CONTEXT_TEXT` (config), zero LLM.
- Supervisor: `out_of_context` para temas externos; `handoff` para universo RecFair sem FAQ/rec.
- Confiança baixa (&lt;0.45) → `out_of_context` (evita transbordo indevido).
- Replans FAQ→handoff e recommend-error→handoff **inalterados** (in-contexto).

## Golden-set

| Mudança | Casos |
| :--- | :--- |
| Reclassificação | T43, T57, T58 → `G_out_of_context` |
| Novos | T59 (fora de contexto), T60 (handoff in-contexto) |
| Inalterado | T56 (handoff — cadastro revendedor) |

Total roteamento: 12 casos (3 rec, 3 FAQ, 2 transbordo, 4 fora de contexto).

## Consequências

- Painel H.4 passa a reportar quatro destinos.
- Baseline multiagent deve ser reexecutado na mesma sessão de eval após deploy.
- `handoff_node` permanece exclusivo para transbordo humano com telefone.
