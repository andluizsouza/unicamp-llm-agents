# RecFair

Sistema de recomendação com contrato **utilidade + justiça** para catálogo de produtos de beleza (dados sintéticos). Desenvolvido no projeto prático **Sistemas Multiagentes** (UNICAMP INF0093).

---

## O que o projeto faz

- Recebe consulta em linguagem natural (ex.: *“shampoos Match mais vendidos abaixo de R$ 50”*).
- Devolve **Top 5** SKUs ranqueados por regras de negócio **ou** abstenção (`RecFairOutput`).
- Mede qualidade em golden-set congelado (**60 casos**, `data/golden/cases.json`) com verify automático (`from eval.verify import verify_case`).

**Arquitetura vigente (E3):** `multiagent` — supervisor + recomendação + FAQ + roteamento.  
**E2 (executável):** `workflow` — LangGraph + scoring determinístico.  
**Baseline (E1):** `baseline` — uma chamada LLM com catálogo/vendas no prompt. As três executáveis.

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
make chat                     # vigente = multiagent (requer GOOGLE_API_KEY)
```

Sem chaves de API: `make lint` e `pytest` cobrem a régua e os contratos. `make data` (índices MiniLM) requer `HF_TOKEN`.

---

## Relatórios de avaliação (entregáveis)

Notebooks são **somente relatório** — importam o pacote, não implementam o sistema.

| Entregável | Notebook | Arquitetura | Conteúdo |
| :--- | :--- | :--- | :--- |
| **E1** | [`eval/notebooks/E1_baseline.ipynb`](eval/notebooks/E1_baseline.ipynb) | `baseline` | Baseline stuffing, 30 casos |
| **E2** | [`eval/notebooks/E2_workflow.ipynb`](eval/notebooks/E2_workflow.ipynb) | `baseline` × `workflow` | Comparação, memória, tools, ADR |
| **E3** | [`eval/notebooks/E3_multiagents.ipynb`](eval/notebooks/E3_multiagents.ipynb) | `baseline` × `workflow` × `multiagent` | Supervisor, FAQ, régua nDCG@5, contextos H.1–H.4 |

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
│   ├── config.py                 ← CURRENT_ARCH=multiagent
│   ├── graphs/
│   │   ├── baseline.py           ← E1
│   │   ├── registry.py
│   │   ├── workflow/             ← E2 LangGraph
│   │   └── multiagent/           ← E3 supervisor
│   ├── tools/scoring/            ← engine.py (ranking determinístico)
│   ├── tools/guardrails.py       ← sanitize_query
│   ├── tools/claims_semantic.py  ← match_substring_or_semantic
│   ├── rag/                      ← FAQ FAISS
│   ├── schemas/                  ← RecFairOutput, ParsedIntent, RoutingDecision
│   ├── prompts/                  ← baseline_v1, workflow_v2, multiagent_v3
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
│   ├── verify/                   ← verify_case, famílias E3
│   ├── report/                   ← painéis HTML para notebooks
│   ├── notebooks/                ← E1_*, E2_*, E3_multiagents
│   └── runs/                     ← JSON por execução
│
├── data/
│   ├── golden/cases.json         ← golden-set (60 casos)
│   ├── tb_catalogo.csv
│   ├── tb_vendas.csv
│   ├── tb_claims.csv             ← E2
│   ├── tb_inventory.csv          ← E2
│   └── claims_manifest.json
│
├── docs/
│   ├── INSTALL.md
│   ├── architecture.md           ← mapa técnico + mermaid
│   └── adr/                      ← decisões datadas (E3 = ADR 0003)
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

Mapa completo com diagramas: [`docs/architecture.md`](docs/architecture.md).

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
- Claims semânticos (T21/T22) e FAQ sem evidência (T44/T46/T47) se o eval mostrar gap persistente.
- Casos T61+ (futuro) para expandir recomendação.
- MCP só com reuso ou fronteira de permissão medida.
