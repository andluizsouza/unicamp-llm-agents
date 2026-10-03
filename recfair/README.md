# RecFair

Sistema de recomendação com contrato **utilidade + justiça** para catálogo de produtos de beleza (dados sintéticos). Desenvolvido no projeto prático **Sistemas Multiagentes** (UNICAMP INF0093).

---

## O que o projeto faz

- Recebe consulta em linguagem natural (ex.: *“shampoos Match mais vendidos abaixo de R$ 50”*).
- Devolve **Top 5** SKUs ranqueados por regras de negócio **ou** abstenção (`RecFairOutput`). A partir do E3 também responde FAQ, transbordo e fora de contexto.
- A régua **atual** é o golden-set de **60 casos** (T01–T60, `data/golden/cases.json`, `golden_revision=3cbcb3e4c4b9cec7`) com verify automático (`from eval.verify import verify_case`). Pares éticos P01–P05 ficam em `data/golden/min_pairs.json`, fora da taxa agregada.

**Arquitetura vigente (E4):** `resilient` — grafo E3 + harness (retry, timeout, degradação, verificadores).  
**E3 (executável):** `multiagent` — supervisor + recomendação + FAQ + roteamento.  
**E2 (executável):** `workflow` — LangGraph determinístico + scoring em 7 passos.  
**Baseline (E1):** `baseline` — uma chamada LLM com catálogo/vendas no prompt. As quatro permanecem executáveis.

### Régua por entrega

O conjunto só cresceu. As saídas gravadas em E1 e E2 são da régua daquela entrega (30 e 38 casos). O `cases.json` de hoje tem 60, e é essa régua que o E4 usa para as quatro versões.

| Entrega | Casos daquela etapa | O que a etapa acrescenta |
| :--- | :--- | :--- |
| **E1** | T01–T30 (30) | Stuffing; gaps de preço, claim, estoque e guardrail previstos |
| **E2** | T01–T38 (38) | Memória T31–T33 e scoring T34–T38; gabarito passa a sair do engine |
| **E3** | T01–T60 (60) | FAQ e roteamento; contextos H.1–H.4 **disjuntos** (somam 60) |
| **E4** | os mesmos T01–T60 | Três rodadas de `resilient`; pares P01–P05 fora da taxa agregada |

Contextos do E3/E4, distintos do Painel A legado (T01–T38 = recomendação + segurança): recomendação T01–T25 e T31–T38 (33); segurança T26–T30 (5); FAQ T39–T40 e T44–T51 (10); roteamento T41–T43 e T52–T60 (12).

---

## Início rápido

Requisito: **Python 3.14** (`.python-version`). Metadados e lint: `pyproject.toml`. Guia passo a passo: [`docs/INSTALL.md`](docs/INSTALL.md).

```bash
cd recfair
python3.14 -m venv venv-recfair
source venv-recfair/bin/activate
cp .env.example .env          # GOOGLE_API_KEY e HF_TOKEN
make install-dev
make kernel                   # Jupyter: kernel "Python (recfair)"
make chat                     # vigente = resilient (requer GOOGLE_API_KEY)
```

Sem chaves de API: `make lint` e `pytest` cobrem a régua e os contratos. `make data` (índices MiniLM) requer `HF_TOKEN`.

---

## Relatórios de avaliação (entregáveis)

Notebooks são **somente relatório** — importam o pacote, não implementam o sistema.

| Entregável | Notebook | Arquitetura | Conteúdo |
| :--- | :--- | :--- | :--- |
| **E1** | [`eval/notebooks/E1_baseline.ipynb`](eval/notebooks/E1_baseline.ipynb) | `baseline` | Stuffing, régua de 30 casos (snapshot da entrega) |
| **E2** | [`eval/notebooks/E2_workflow.ipynb`](eval/notebooks/E2_workflow.ipynb) | `baseline` × `workflow` | Workflow, memória, tools locais, régua de 38 |
| **E3** | [`eval/notebooks/E3_multiagents.ipynb`](eval/notebooks/E3_multiagents.ipynb) | `baseline` × `workflow` × `multiagent` | Supervisor, FAQ, nDCG@5, contextos H.1–H.4, 60 casos |
| **E4** | [`eval/notebooks/E4_robustez_etica.ipynb`](eval/notebooks/E4_robustez_etica.ipynb) | as quatro, `resilient` em 3 rodadas | Contenção, Wilson, ética, recomendação; consolidação em `54bcd4958950` (46/60) |

Reproduzir eval: abrir o notebook da entrega e executar células com `run_eval(arch=...)`. Requer `GOOGLE_API_KEY`. Não há `make eval`.

```bash
make data    # CSVs + índices FAISS (claims e FAQ) — exporta HF_TOKEN do .env
make chat ARCH=workflow
make chat ARCH=baseline
```

---

## CLI (`make chat`)

UI Rich no terminal. Entry: `python -m recfair.cli`.

**Comandos:** `/quit` · `/reset` · `/trace` · `/arch <id>`

**Exibe por turno:** consulta, tools acionadas (nome + args), saída estruturada (`RecFairOutput`), latência, `halt_reason` se houver. `/trace` mostra traces de agente e scoring.

---

## Estrutura de pastas

```
recfair/                          ← raiz do app (abra esta pasta no IDE)
├── README.md                     ← este arquivo
├── Makefile                      ← install, chat, lint, data, kernel
├── pyproject.toml                ← metadados do pacote + ruff
├── .python-version               ← 3.14
├── requirements.txt
├── requirements-dev.txt
├── .env.example                  ← GOOGLE_API_KEY + HF_TOKEN (não commitar .env)
│
├── recfair/                      ← pacote Python (runtime)
│   ├── cli.py                    ← make chat
│   ├── config.py                 ← CURRENT_ARCH=resilient
│   ├── graphs/
│   │   ├── baseline.py           ← E1
│   │   ├── registry.py
│   │   ├── workflow/             ← E2 LangGraph
│   │   ├── multiagent/           ← E3 supervisor
│   │   └── resilient/            ← E4 harness runner
│   ├── harness/                  ← retry, timeout, degrade, verify
│   ├── tools/scoring/            ← engine.py (ranking determinístico)
│   ├── tools/guardrails.py       ← sanitize_query
│   ├── tools/claims_semantic.py  ← match_substring_or_semantic
│   ├── rag/                      ← FAQ FAISS
│   ├── schemas/                  ← RecFairOutput, ParsedIntent, RoutingDecision
│   ├── prompts/                  ← baseline_v1, workflow_v2, multiagent_v3, multiagent_v4
│   ├── data/                     ← gera CSV/SQLite
│   └── observability/
│
├── eval/
│   ├── runner.py                 ← run_eval()
│   ├── metrics.py                ← nDCG@5, severity
│   ├── requirements.py           ← RF-01–RF-07
│   ├── gold.py                   ← gabarito → engine
│   ├── contexts.py               ← contextos H.1–H.4
│   ├── glossary.py               ← glossário de métricas
│   ├── stats.py                  ← Wilson / overlap (E4)
│   ├── reliability.py            ← 3 runs + casos instáveis (E4)
│   ├── ethics.py                 ← pesos, pares mínimos, matriz (E4)
│   ├── verify/                   ← verify_case, famílias E3
│   ├── report/                   ← painéis HTML para notebooks
│   ├── notebooks/                ← E1_*, E2_*, E3_*, E4_robustez_etica
│   └── runs/                     ← JSON por execução
│
├── data/
│   ├── golden/cases.json         ← golden-set (60 casos, T01–T60)
│   ├── golden/min_pairs.json     ← pares mínimos E4 (ética)
│   ├── tb_catalogo.csv
│   ├── tb_vendas.csv
│   ├── tb_claims.csv             ← E2
│   ├── tb_inventory.csv          ← E2
│   └── claims_manifest.json
│
├── docs/
│   ├── INSTALL.md
│   ├── architecture.md           ← mapa técnico + mermaid
│   └── adr/                      ← decisões datadas (E4 = ADR 0004)
│
└── tests/
```

Ambiente virtual: `venv-recfair/` (criado localmente, não versionado). Interpretador IDE: `.vscode/settings.json` → `venv-recfair/bin/python`.

---

## Arquiteturas registradas

| id | Entregável | Descrição | ADR |
| :--- | :--- | :--- | :--- |
| `baseline` | E1 | 1× LLM, stuffing CSV, sem tools | [0001](docs/adr/0001-baseline.md) |
| `workflow` | E2 | LangGraph, intent LLM + scoring 7 passos, memória | [0002](docs/adr/0002-workflow-scoring.md) |
| `multiagent` | E3 | Supervisor + FAQ RAG + guardrail + claims embed + roteamento | [0003](docs/adr/0003-multiagent-supervisor.md) |
| `resilient` | E4 | Grafo E3 + harness (retry/timeout/degrade/verify) + prompt v4 | [0004](docs/adr/0004-resilient-harness.md) |

Mapa completo com diagramas: [`docs/architecture.md`](docs/architecture.md).

`recfair.config.CURRENT_ARCH` = **`resilient`**. `make chat` (sem `ARCH`) usa a vigente. E3: `make chat ARCH=multiagent`. Baseline: `make chat ARCH=baseline`.

---

## Comandos úteis

| Comando | Efeito |
| :--- | :--- |
| `make help` | Lista alvos |
| `make install` / `make install-dev` | Dependências |
| `make chat ARCH=<id>` | UI terminal |
| `make lint` / `make format` | Ruff |
| `make data` | Regenera CSVs e índices FAISS (claims + FAQ) |
| `make kernel` | Kernel Jupyter |

Não há `make eval` — golden-set roda nos notebooks via `eval.runner.run_eval`.

---

## O que não está no sistema

Lista e motivo em [`docs/architecture.md`](docs/architecture.md) (seção “Deliberadamente fora do E4”) e no [ADR 0004](docs/adr/0004-resilient-harness.md): fairness auditor, MCP, memória de longo prazo, mutação da régua T01–T60.
