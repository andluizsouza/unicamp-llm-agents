# Arquitetura RecFair

**Última atualização:** 2026-10-03 (evidência do E4 e faixas H.1–H.4; a promoção de `resilient` continua 2026-09-27)  
**Arquitetura vigente (`CURRENT_ARCH`):** `resilient` · data 2026-09-27 · ADR [0004](adr/0004-resilient-harness.md) (E4: harness + ética)  
**Ainda executáveis:** `multiagent` · 2026-09-19 · ADR [0003](adr/0003-multiagent-supervisor.md) · `workflow` · 2026-09-13 · ADR [0002](adr/0002-workflow-scoring.md) · `baseline` · 2026-09-07 · ADR [0001](adr/0001-baseline.md)

RecFair é um assistente de recomendação Top-5 para catálogo de beleza (Grupo Boticário, dados sintéticos), com FAQ de e-commerce/revenda, transbordo humano, redirecionamento fora de contexto e, no E4, contenção de falhas com resposta degradada rotulada. Toda arquitetura expõe `RecFairOutput` e é medida pelo golden-set em `data/golden/cases.json` (**60 casos**, T01–T60). Perfil capilar e demais eixos de paridade estão em `data/golden/min_pairs.json` (P01–P05), fora da taxa agregada.

---

## Visão geral das arquiteturas

| | `baseline` (E1) | `workflow` (E2) | `multiagent` (E3) | `resilient` (E4, vigente) |
| :--- | :--- | :--- | :--- | :--- |
| **Padrão** | Monolito — 1× LLM | LangGraph — LLM só em `parse_intent` | Supervisor — 3 agentes + 3 nós | Mesmo grafo E3 + harness |
| **Dados no prompt** | Catálogo + vendas (~29k tokens) | Query NL | Query sanitizada + skills / FAQ | Idem E3; prompt `v4` (equidade) |
| **Ranking** | Modelo no prompt | `engine.py` (substring claims) | Engine E2 + `semantic_fallback` | Idem E3 |
| **Guardrail** | Não | Não | `security_node` regex/redact | Idem + verify pós-grafo |
| **FAQ / handoff / out_of_context** | Não | Não | Agente FAQ + nós template | Idem; FAQ instável → degradado |
| **Contenção** | Schema inválido → abstenção | `recursion_limit=12` | `recursion_limit=16` | Retry + timeout nos adapters; verify pós-`invoke` |
| **Memória** | Stateless | `MemorySaver` | `MemorySaver` | Mesmo checkpointer E3 |
| **Prompt** | `baseline_v1` | `workflow_v2` | `multiagent_v3` | `multiagent_v4` |
| **ADR** | [0001](adr/0001-baseline.md) | [0002](adr/0002-workflow-scoring.md) | [0003](adr/0003-multiagent-supervisor.md) | [0004](adr/0004-resilient-harness.md) |
| **Relatório eval** | [E1_baseline.ipynb](../eval/notebooks/E1_baseline.ipynb) | [E2_workflow.ipynb](../eval/notebooks/E2_workflow.ipynb) | [E3_multiagents.ipynb](../eval/notebooks/E3_multiagents.ipynb) | [E4_robustez_etica.ipynb](../eval/notebooks/E4_robustez_etica.ipynb) |

---

## Mapa de módulos (código)

```
recfair/
├── cli.py                      # default = vigente (resilient)
├── config.py                   # CURRENT_ARCH=resilient
├── graphs/
│   ├── registry.py
│   ├── baseline.py
│   ├── workflow/
│   ├── multiagent/             # E3
│   └── resilient/              # E4 runner
├── harness/                    # retry, timeout, degrade, verify
├── tools/
│   ├── scoring/engine.py
│   ├── guardrails.py
│   └── claims_semantic.py
├── rag/
├── schemas/
├── prompts/                    # … + multiagent_v4
└── observability/agent_trace.py

eval/
├── runner.py
├── stats.py / reliability.py / ethics.py
├── report/e4_panels.py
└── notebooks/E4_robustez_etica.ipynb
```

---

## Arquitetura `resilient` (E4, vigente)

**Decisão:** ADR [0004](adr/0004-resilient-harness.md) §§3.1–3.4. Não há grafo novo. O harness é a política de falha em volta da política de domínio do E3: `graphs/resilient/runner.py` compila o LangGraph E3 e liga o pacote `recfair/harness/` só naquela chamada. Com o escopo desligado, o mesmo grafo continua sendo o `multiagent`.

**Componentes:**

| Peça | Onde | Papel |
| :--- | :--- | :--- |
| Escopo | `harness/context.py` | `ContextVar`; default desligado, então `ARCH=multiagent` não retenta |
| Adapters | `harness/adapters.py` | Timeout + retry no LLM estruturado e no retrieve FAQ |
| Retry | `harness/retry.py` | Só falha transitória; backoff exponencial |
| Timeout | `harness/timeout.py` | Thread daemon; estouro → `TimeoutExpired` |
| Injeção | `harness/unstable.py` | `FonteIndisponivel` com `RECFAIR_INJECT_FAILURE_PROB` (default 0) |
| Degradação | `harness/degrade.py` | Prefixo `[Resposta parcial]`, `degraded=True` |
| Citações | `harness/citations.py` | Claims do SKU ou excerpts da FAQ |
| Verify | `harness/verify_output.py` | `verify_evidence` + `verify_confidence` após o `invoke` |
| Prompt | `prompts/multiagent_v4.py` | Equidade; `dispatch.py` só escolhe v4 com o harness ligado |

**Ganho esperado:** contenção demonstrável sem LLM; falha silenciosa vira handoff rotulado. Empate de nDCG@5 no escopo de recomendação, dentro do intervalo de Wilson, é resultado válido.

**Resultado registrado (2026-10-03):** três rodadas full em [`eval/notebooks/E4_robustez_etica.ipynb`](../eval/notebooks/E4_robustez_etica.ipynb) — `003a48fb5114` (44/60), `ad5ead0575f6` (43/60), `54bcd4958950` (46/60). A consolidação usa a terceira. nDCG@5 nos 33 casos de recomendação: 0,9641 (E3) e 0,9654 (E4). Wilson 95% de E3 e E4 se sobrepõe. Contenção sem LLM: `tests/test_harness.py`. Os JSON de `eval/runs/` não vão para o git.

### Fluxo do runner

O verify **não** é nó do LangGraph. Roda em `_post_process` quando o `invoke` devolve state.

```mermaid
flowchart TD
    scope[harness_scope] --> invoke[grafo E3]
    invoke -->|exceção no supervisor| esc[timeout_output ou tool_error_output]
    invoke -->|FAQ capturou a falha| post[_post_process]
    invoke -->|ok| post
    post --> checks[citações + dois verificadores]
    checks -->|issue| deg["handoff halt=degraded"]
    post -->|FAQ replanejada| lab["label_degraded halt=degraded"]
```

Injeção de FAQ (`FonteIndisponivel`) não chega ao `except` do runner: `faq_node` transforma em handoff e o pós-processo só acrescenta o rótulo `[Resposta parcial]`. `timeout_output` / `tool_error_output` cobrem exceção que escapa do grafo (supervisor).

### Grafo (o mesmo do E3)

```mermaid
flowchart TD
    START([query]) --> SEC[security_node]
    SEC --> SUP[supervisor]
    SUP --> ROUTE{domain}
    ROUTE -->|recommendation| REC[recommendation]
    ROUTE -->|faq| FAQ[faq]
    ROUTE -->|out_of_context| OOC[out_of_context]
    ROUTE -->|handoff| HO[handoff]
    FAQ -->|no_evidence ou error| HO
    REC -->|error| HO
    REC --> ENDN([END])
    FAQ --> ENDN
    OOC --> ENDN
    HO --> ENDN
```

**Controles:** `recursion_limit=16`; timeout LLM 45 s e FAQ 20 s; até 3 retries extras só em falha transitória; injeção de falha default 0. Checkpointer in-memory igual ao E3.

### Prompt e tools

Supervisor e FAQ leem `prompts/dispatch.py`. Harness ligado → `multiagent_v4` (não inferir gênero, idade, registro ou tipo de cabelo para piorar a rota). Harness desligado → `multiagent_v3`. Ranking, guardrail, RAG e scoring são os do E3; o harness só embrulha o `invoke` do LLM e o `retrieve_faq`.

---

## Arquitetura `multiagent` (E3)

**Objetivo:** atacar domínio único, claims substring e ausência de guardrail **sem** reescrever o ranking E2.

**Ganho esperado:** T26–T30 com sanitização real; T39–T60 (FAQ/roteamento/handoff/out_of_context) >0%; T18/T21/T22 parciais. Painel A (T01–T38) pode empatar ou cair 0–2 pp por roteamento — resultado válido.

**Resultado de eval ponta a ponta:** documentado em [`eval/notebooks/E3_multiagents.ipynb`](../eval/notebooks/E3_multiagents.ipynb) (seção H). Testes unitários da régua e dos guardrails não usam LLM.

### Grafo LangGraph

```mermaid
flowchart TD
    START([query]) --> SEC[security_node]
    SEC --> SUP[supervisor_agent]
    SUP --> ROUTE{RoutingDecision.domain}
    ROUTE -->|recommendation| REC[recommendation_agent]
    ROUTE -->|faq| FAQ[faq_agent]
    ROUTE -->|out_of_context| OOC[out_of_context_node]
    ROUTE -->|handoff| HO[handoff_node]
    FAQ -->|no_evidence ou error| HO
    REC -->|error| HO
    REC --> END([END])
    FAQ --> END
    OOC --> END
    HO --> END
```

O nó compilado é `recommendation` (`recommendation_node`). Por dentro ele chama `parse_intent`, o engine e a síntese. `route_after_recommend` manda `last_result.status=error` para `handoff`; `route_after_faq` faz o mesmo para `no_evidence` e `error`.

**Controles:** `recursion_limit=16`; um replanejamento FAQ→handoff (`replanned=True` no contrato); skills carregadas só depois do roteamento (`load_skill`); especialistas gravam `last_result: AgentResult`.

**Resultado na régua de 60:** manifest `ae3f3348d3e4` (41/60), mesma sessão dos canônicos E1/E2 citados no ADR 0004. Leitura por contexto no notebook E3, seção H.

### Por que segurança, out_of_context e handoff não são agentes

Não passam no teste de 4 colunas (escopo / tools / instrução / avaliação isolada): são regex+redact e templates fixos, sem raciocínio LLM. `out_of_context` redireciona perguntas externas; `handoff` transborda in-contexto com telefone (ADR 0003 §3.3).

### Pipeline de recomendação (interno ao especialista)

Reusa `parse_intent` E2 + `score_recommendation(..., semantic_fallback=True)` + synthesize. Substring é a régua (igual E2/gold); fallback semântico via `match_substring_or_semantic` por SKU só quando nenhum item do pool acerta substring. Oráculos de paráfrase ficam em `tests/test_claims_semantic.py`, fora do H.1.

### Memória

Cada grafo tem o seu `MemorySaver`. O mecanismo é o do E2: `thread_id` isola a conversa e `session_intent` vive no `parse_intent` da recomendação. T09 e T31 ficaram fora deste incremento.

```mermaid
flowchart LR
    Q[query + thread_id] --> CP[(MemorySaver)]
    CP --> PI[parse_intent]
    PI --> SI[session_intent]
    SI -.->|proximo turno| PI
```

### Tools locais vs MCP

Guardrail (`sanitize_query`), claims embed, retrieve_faq e scoring são funções in-process. MCP recusado: um consumidor, dados empacotados, sem fronteira de permissão (ADR 0003).

---

## Arquitetura `baseline` (E1)

**Decisão:** ADR [0001](adr/0001-baseline.md). Uma chamada Gemini com catálogo e vendas no prompt, saída `RecFairOutput`. Componentes: `graphs/baseline.py`, `prompts/baseline_v1.py`. Sem LangGraph, tools, memória, claims, inventory ou FAQ.

```mermaid
flowchart LR
    Q[Query NL] --> PROMPT[build_prompt baseline_v1]
    CAT[(tb_catalogo)] --> PROMPT
    SAL[(tb_vendas)] --> PROMPT
    PROMPT --> LLM[ChatGoogleGenerativeAI]
    LLM --> OUT[RecFairOutput]
```

**Ganho esperado:** baseline honesto de interpretação NL, com contrato estável para as versões seguintes.

**Evidência:** snapshot da entrega em [`eval/notebooks/E1_baseline.ipynb`](../eval/notebooks/E1_baseline.ipynb) — run `c7d7221e612b`, 15/30 no overall e 9/15 no restrito (`golden_revision=cedba68fb6c4c54c`). Reexecução na régua de 38: `00b767134d22` (7/38). Na régua de 60: `c6d86c0d894f` (11/60).

---

## Arquitetura `workflow` (E2)

**Decisão:** ADR [0002](adr/0002-workflow-scoring.md). LLM só em `parse_intent` (`prompts/workflow_v2.py`); ranking em `tools/scoring/engine.py`. Grafo em `graphs/workflow/` — nós compilados `parse_intent`, `score`, `abstain`, `synthesize`. `recursion_limit=12`.

```mermaid
flowchart TD
    START([START]) --> PI[parse_intent]
    PI --> ROUTE{route_after_intent}
    ROUTE -->|abstain| AB[abstain]
    ROUTE -->|score| SC[score]
    SC --> SY[synthesize]
    AB --> END1([END])
    SY --> END2([END])
```

### Pipeline de tools

Os sete passos são uma tool lógica (`score_recommendation`). `eval/gold.py` chama o mesmo engine com matcher por substring. O fallback semântico existe só no caminho multiagent.

```mermaid
flowchart LR
    subgraph steps [engine.py]
        direction TB
        s1[filter] --> s2[exclude]
        s2 --> s3[claims]
        s3 --> s4[diversity]
        s4 --> s5[promo]
        s5 --> s6[rank]
        s6 --> s7[top5]
    end
    DB[(SQLite e CSV)] --> steps
    steps --> TR[ScoreTrace]
```

### Memória

`MemorySaver` + `thread_id`. O invoke não reenvia `session_intent` vazio: um dict vazio apagaria o checkpoint no turno seguinte. T31–T33 são o caso que justifica o incremento.

```mermaid
flowchart LR
    T[turno N + thread_id] --> CP[(MemorySaver)]
    CP --> PI[parse_intent]
    PI --> SI[session_intent]
    SI -.->|turno N+1| CP
```

**Ganho esperado:** agregação, filtros e claims deixam de depender do modelo; prompt curto; trace por SKU.

**Evidência:** régua de 38 casos no [`eval/notebooks/E2_workflow.ipynb`](../eval/notebooks/E2_workflow.ipynb) — workflow `d79563e06651` (76,3% overall) contra baseline `00b767134d22` (18,4%), `golden_revision=15f3ed6986de9ce9`. Na régua de 60 o workflow é `6d5cb78a9e25` (31/60): FAQ e roteamento entram só no E3.

---

## Contrato de saída

`RecFairOutput` (`recfair/schemas/output.py`):

- `status`: `recommendation` | `abstention` | `faq` | `handoff` | `out_of_context`
- `items[]`: Top-5 ou vazio
- `answer_text` / `handoff_phone` / `agents_route`: campos E3 opcionais (default vazio)
- `degraded` / `degraded_reason` / `citations`: campos E4 (default off). `halt_reason` aceita também `timeout`, `degraded`, `tool_error`
- T01–T38 continuam usando só `recommendation`/`abstention`

Contrato entre agentes: `RoutingDecision` e `AgentResult` em `schemas/routing.py`. O grafo persiste `last_result` em cada especialista; FAQ `no_evidence`/`error` e recomendação `error` roteiam para `handoff_node`. Perguntas totalmente fora de O Boticário vão para `out_of_context_node` (template fixo, sem telefone).

---

## Avaliação (ADR 0003 §3.2)

Régua principal E3: **nDCG@5** (média por escopo) + `aprovado_exact` + `severity` + breakdown RF-01–RF-07 + `gap_intentional_pass` em T16–T30.

Escopos legado (T01–T38): `restrict_core` T01–T15 · `gap` T16–T30 · `memory` T31–T33 · `scoring` T34–T38 · `overall` T01–T38.

### Contextos de avaliação E3 (H.1–H.4)

Definidos em `eval/contexts.py`:

```mermaid
flowchart LR
    H1[H.1 recomendacao] --> R[T01-T25 e T31-T38]
    H2[H.2 seguranca] --> S[T26-T30]
    H3[H.3 faq] --> F[T39-T40 e T44-T51]
    H4[H.4 roteamento] --> T[T41-T43 e T52-T60]
```

| Contexto | Casos | n | Arquiteturas medidas |
| :--- | :--- | ---: | :--- |
| `recomendacao` | T01–T25, T31–T38 | 33 | baseline, workflow, multiagent, resilient |
| `seguranca` | T26–T30 | 5 | baseline, workflow, multiagent, resilient |
| `faq` | T39–T40, T44–T51 | 10 | multiagent, resilient |
| `roteamento` | T41–T43, T52–T60 | 12 | multiagent, resilient |

As quatro faixas são disjuntas e somam 60. O Painel A (T01–T38) reúne H.1 e H.2 e permanece a comparação legada com o E2. H.1–H.4 organizam os notebooks E3 e E4. FAQ e roteamento medem só `multiagent` e `resilient` (`CONTEXT_ARCHITECTURES` em `eval/contexts.py`).

`e1_rate_*` / `e2_rate_*` permanecem no manifest. Métricas **não** vivem no notebook.

Golden-set: T01–T38 imutáveis; T39–T60 acrescentados em fases (ver ADR 0003 §4.4). Hash `golden_revision` em cada run.

### Avaliação E4 (ADR 0004 §4.7)

A régua T01–T60 e `verify_case` não mudam. O que entra é leitura extra, fora da taxa agregada quando o eixo não é a régua:

| Módulo | O que mede |
| :--- | :--- |
| `eval/stats.py` | Intervalo de Wilson e se dois intervalos se sobrepõem |
| `eval/reliability.py` | Três rodadas da mesma arch; casos que mudam de aprovado |
| `eval/ethics.py` | Peso de dano 0–5, score ponderado, pares P01–P05 |
| `data/golden/min_pairs.json` | Paridade (cabelo, gênero, idade, registro); ouro compartilhado |

Manifests canônicos na régua de 60 casos (`golden_revision=3cbcb3e4c4b9cec7`): `c6d86c0d894f` (E1, 11/60), `6d5cb78a9e25` (E2, 31/60), `ae3f3348d3e4` (E3, 41/60), `54bcd4958950` (E4, rodada de consolidação, 46/60). As outras rodadas E4 são `003a48fb5114` (44/60) e `ad5ead0575f6` (43/60).

---

## Dados

| Artefato | Uso |
| :--- | :--- |
| `tb_catalogo`, `tb_vendas` | baseline + engine |
| `tb_claims`, `tb_inventory` | engine passos 2–5 |
| `data/kb/faq.pdf`, `revenda.md` | RAG FAQ (LangChain: `PyPDFLoader` + `RecursiveCharacterTextSplitter`; PDF 1024/120, revenda 512/60; MiniLM + FAISS COSINE; k=5) |
| `data/indexes/` | FAISS claims+FAQ (gitignored; `make data`) |

Regenerar: `make data` (CSVs **e** índices). O MiniLM autentica no Hugging Face Hub com `HF_TOKEN` (exportado do `.env` pelo Makefile e por `export_hf_token()`).

---

## Evidência de eval

| Artefato | Conteúdo |
| :--- | :--- |
| [E2_workflow.ipynb](../eval/notebooks/E2_workflow.ipynb) | Comparação E1×E2 (régua então vigente) |
| [E4_robustez_etica.ipynb](../eval/notebooks/E4_robustez_etica.ipynb) | Seções A–K: contenção, 3 runs, Wilson, ética, quatro versões |
| [E3_multiagents.ipynb](../eval/notebooks/E3_multiagents.ipynb) | Seções A–J + contextos H.1–H.4 + régua `e3_*`; `run_eval` das três arches |
| [E1_baseline.ipynb](../eval/notebooks/E1_baseline.ipynb) | Relatório E1 (intacto) |

Runs JSON em `eval/runs/` (gitignore). Sem API key, o notebook documenta o caminho e os testes unitários substituem o smoke da régua.

---

## Observabilidade

| Canal | O quê |
| :--- | :--- |
| `AgentTrace` | latência, LLM, tools, tokens por `agent_id` |
| `ScoreTrace` | bônus/exclusões do engine |
| CLI `/trace` | output + traces; linha de status mostra `degradado` |
| Manifest | `resumo` legado + `resumo_v3` |

---

## Hard-stops e humano no circuito

RecFair não conclui compra. O telefone de transbordo é o corte para a pessoa.

| Arquitetura | O que interrompe o turno |
| :--- | :--- |
| `baseline` | Saída que não valida o schema → abstenção |
| `workflow` | `recursion_limit=12`; schema inválido → abstenção |
| `multiagent` | `recursion_limit=16`; um replan FAQ→handoff; confiança do supervisor abaixo de 0,45 → `out_of_context` |
| `resilient` | Os limites do E3, mais timeout por operação, retry só em falha transitória, e handoff quando o verificador discorda da fonte |

No E4 o usuário vê `[Resposta parcial]` e o telefone quando o prazo estoura, a tool esgota o retry, ou a citação não está na fonte. Confirmar cada passo do ranking fica de fora: transferiria a lista inteira para quem pergunta.

---

## Executar

```bash
make chat                 # vigente → resilient (ARCH=current)
make chat ARCH=multiagent
make chat ARCH=workflow
make chat ARCH=baseline
make data                 # CSVs + FAISS
```

Golden-set: [`eval/notebooks/E4_robustez_etica.ipynb`](../eval/notebooks/E4_robustez_etica.ipynb) chama `eval.runner.run_eval` — não há `make eval`.

---

## Deliberadamente fora do E4

| Peça | Motivo |
| :--- | :--- |
| Fairness auditor (agente) | E4 mede dano no eval; ADR 0003 já recusou |
| MCP | Sem reuso nem fronteira |
| Memória de longo prazo | Checkpointer in-memory; accountability via `eval/runs/` |
| `multiagent_v2` | Experimento de retrieval; não está no registry |
| Mutar `verify_case` na régua T01–T60 | Skill: comparação principal herdada |

---

## Histórico de arquiteturas

| id | data | ADR | Status |
| :--- | :--- | :--- | :--- |
| `baseline` | 2026-09-07 | [0001](adr/0001-baseline.md) | executável (`ARCH=baseline`) |
| `workflow` | 2026-09-13 | [0002](adr/0002-workflow-scoring.md) | executável (`ARCH=workflow`) |
| `multiagent` | 2026-09-19 | [0003](adr/0003-multiagent-supervisor.md) | executável (`ARCH=multiagent`) |
| `resilient` | 2026-09-27 | [0004](adr/0004-resilient-harness.md) | **vigente** (`CURRENT_ARCH`) |
