# RecFair

Sistema de recomendação com contrato **utilidade + justiça** para catálogo de produtos de beleza (dados sintéticos). Desenvolvido no projeto prático **Sistemas Multiagentes** (UNICAMP INF0093).

---

## O que o projeto faz

- Recebe consulta em linguagem natural (ex.: *“shampoos Match mais vendidos abaixo de R$ 50”*).
- Devolve **Top 5** SKUs ranqueados por regras de negócio **ou** abstenção (`RecFairOutput`).
- Mede qualidade em golden-set congelado (`data/golden/cases.json`) com verify automático (`eval/verify.py`).

**Arquitetura vigente (E3):** `multiagent` — supervisor + recomendação + FAQ.  
**E2 (executável):** `workflow` — LangGraph + scoring determinístico.  
**Baseline (E1):** `baseline` — uma chamada LLM com catálogo/vendas no prompt. As três executáveis.

---

## Início rápido

Requisito: **Python 3.14**. Guia passo a passo: [`docs/INSTALL.md`](docs/INSTALL.md).

```bash
cd recfair
python3.14 -m venv venv-recfair
source venv-recfair/bin/activate
cp .env.example .env          # GOOGLE_API_KEY e HF_TOKEN
make install-dev
make kernel                   # Jupyter: kernel "Python (recfair)"
```

---

## Relatórios de avaliação (entregáveis)

Notebooks são **somente relatório** — importam o pacote, não implementam o sistema.

| Entregável | Notebook | Arquitetura | Conteúdo |
| :--- | :--- | :--- | :--- |
| **E1** | [`eval/notebooks/E1_baseline.ipynb`](eval/notebooks/E1_baseline.ipynb) | `baseline` | Baseline stuffing, 30 casos |
| **E2** | [`eval/notebooks/E2_workflow.ipynb`](eval/notebooks/E2_workflow.ipynb) | `baseline` × `workflow` | Comparação, memória, tools, ADR |
| **E3** | [`eval/notebooks/E3_evaluation.ipynb`](eval/notebooks/E3_evaluation.ipynb) | `baseline` × `workflow` × `multiagent` | Supervisor, FAQ, régua nDCG@5 |

Reproduzir eval: abrir o notebook da entrega e executar células com `run_eval(arch=...)`. Requer `GOOGLE_API_KEY`. `make data` (índices MiniLM) requer `HF_TOKEN`. Sem as chaves, `make lint` e `pytest` cobrem a régua e os contratos.

```bash
make data    # CSVs + índices FAISS (claims e FAQ) — exporta HF_TOKEN do .env
make chat    # vigente = multiagent
make chat ARCH=workflow
make chat ARCH=baseline
```

---

## Estrutura de pastas

```
recfair/                          ← raiz do app (abra esta pasta no IDE)
├── README.md                     ← este arquivo
├── Makefile                      ← install, chat, lint, data, kernel
├── requirements.txt
├── requirements-dev.txt
├── .env.example                  ← GOOGLE_API_KEY + HF_TOKEN (não commitar .env)
│
├── recfair/                      ← pacote Python (runtime)
│   ├── cli.py                    ← make chat
│   ├── config.py                 ← CURRENT_ARCH=multiagent
│   ├── graphs/
│   │   ├── baseline.py           ← E1
│   │   ├── registry.py
│   │   ├── workflow/             ← E2 LangGraph
│   │   └── multiagent/           ← E3 supervisor
│   ├── tools/scoring/            ← engine.py (ranking determinístico)
│   ├── rag/                      ← FAQ FAISS
│   ├── schemas/                  ← RecFairOutput, ParsedIntent, RoutingDecision
│   ├── prompts/                  ← baseline_v1, workflow_v2, multiagent_v3
│   ├── data/                     ← gera CSV/SQLite
│   └── observability/
│
├── eval/
│   ├── runner.py                 ← run_eval()
│   ├── verify.py                 ← régua RF-* + gaps
│   ├── gold.py                   ← gabarito → engine
│   ├── report.py                 ← HTML para notebooks
│   ├── notebooks/                ← E1_*, E2_* (relatórios)
│   └── runs/                     ← JSON por execução
│
├── data/
│   ├── golden/cases.json         ← golden-set
│   ├── tb_catalogo.csv
│   ├── tb_vendas.csv
│   ├── tb_claims.csv             ← E2
│   ├── tb_inventory.csv          ← E2
│   └── claims_manifest.json
│
├── docs/
│   ├── INSTALL.md
│   ├── architecture.md           ← mapa técnico + mermaid
│   └── adr/                      ← decisões datadas
│
└── tests/
```

Ambiente virtual: `venv-recfair/` (criado localmente, não versionado).

---

## Arquiteturas registradas

| id | Entregável | Descrição | ADR |
| :--- | :--- | :--- | :--- |
| `baseline` | E1 | 1× LLM, stuffing CSV, sem tools | [0001](docs/adr/0001-baseline.md) |
| `workflow` | E2 | LangGraph, intent LLM + scoring 7 passos, memória | [0002](docs/adr/0002-workflow-scoring.md) |
| `multiagent` | E3 | Supervisor + FAQ RAG + guardrail + claims embed | [0003](docs/adr/0003-multiagent-supervisor.md) |

Mapa completo com diagramas: [`docs/architecture.md`](docs/architecture.md). Régua E3: [0004](docs/adr/0004-layered-evaluation-metrics.md).

`recfair.config.CURRENT_ARCH` = **`multiagent`**. `make chat` (sem `ARCH`) usa a vigente. Baseline: `make chat ARCH=baseline`.

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

## Evolução prevista (E4+)

Documentado em [`docs/architecture.md`](docs/architecture.md) e ADR 0003:

- Correção de intent/memória (T09, T31) se o Painel A exigir.
- T44–T46 (handoff por FAQ sem evidência, paráfrases de claims) se o eval mostrar gap.
- MCP só com reuso ou fronteira de permissão medida.

---