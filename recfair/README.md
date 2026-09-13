# RecFair

Sistema de recomendação com contrato **utilidade + justiça** para catálogo de produtos de beleza (dados sintéticos). Desenvolvido no projeto prático **Sistemas Multiagentes** (UNICAMP INF0093).

---

## O que o projeto faz

- Recebe consulta em linguagem natural (ex.: *“shampoos Match mais vendidos abaixo de R$ 50”*).
- Devolve **Top 5** SKUs ranqueados por regras de negócio **ou** abstenção (`RecFairOutput`).
- Mede qualidade em golden-set congelado (`data/golden/cases.json`) com verify automático (`eval/verify.py`).

**Arquitetura vigente (E2):** `workflow` — LangGraph + scoring determinístico.  
**Baseline (E1):** `baseline` — uma chamada LLM com catálogo/vendas no prompt. Ambas executáveis.

---

## Início rápido

Requisito: **Python 3.14**. Guia passo a passo: [`docs/INSTALL.md`](docs/INSTALL.md).

```bash
cd recfair
python3.14 -m venv venv-recfair
source venv-recfair/bin/activate
cp .env.example .env          # GOOGLE_API_KEY
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

Reproduzir eval: abrir notebook E2 e executar células com `run_eval(arch=...)`.

---

## Estrutura de pastas

```
recfair/                          ← raiz do app (abra esta pasta no IDE)
├── README.md                     ← este arquivo
├── Makefile                      ← install, chat, lint, data, kernel
├── requirements.txt
├── requirements-dev.txt
├── .env.example                  ← GOOGLE_API_KEY (não commitar .env)
│
├── recfair/                      ← pacote Python (runtime)
│   ├── cli.py                    ← make chat
│   ├── config.py                 ← CURRENT_ARCH=workflow
│   ├── graphs/
│   │   ├── baseline.py           ← E1
│   │   ├── registry.py
│   │   └── workflow/             ← E2 LangGraph
│   ├── tools/scoring/            ← engine.py (ranking determinístico)
│   ├── schemas/                  ← RecFairOutput, ParsedIntent
│   ├── prompts/                  ← baseline_v1, workflow_v2
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

Mapa completo com diagramas: [`docs/architecture.md`](docs/architecture.md).

`recfair.config.CURRENT_ARCH` = **`workflow`**. Use `make chat ARCH=current` ou `ARCH=workflow`.

---

## Comandos úteis

| Comando | Efeito |
| :--- | :--- |
| `make help` | Lista alvos |
| `make install` / `make install-dev` | Dependências |
| `make chat ARCH=<id>` | UI terminal |
| `make lint` / `make format` | Ruff |
| `make data` | Regenera CSVs |
| `make kernel` | Kernel Jupyter |

Não há `make eval` — golden-set roda nos notebooks via `eval.runner.run_eval`.

---

## Evolução prevista (E3+)

Documentado em [`docs/architecture.md`](docs/architecture.md) e ADR 0002:

- Agente especializado **match de claims** (substituir regex).
- Agente **segurança/privacidade** + guardrails (T26–T30).
- MCP opcional se houver integração externa compartilhada.

---