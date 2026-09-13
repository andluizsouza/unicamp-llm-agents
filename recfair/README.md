# RecFair

Sistema de recomendação com contrato utilidade + justiça (Entregável 1 — baseline).

## Instalação

Requisito: **Python 3.14**. Guia completo em [`docs/INSTALL.md`](docs/INSTALL.md).

```bash
python3.14 -m venv venv-recfair
source venv-recfair/bin/activate
cp .env.example .env   # preencha GOOGLE_API_KEY
make install-dev
make kernel            # kernel Jupyter "Python (recfair)"
```

O ambiente virtual fica em `recfair/venv-recfair/` (não versionado).

**Cursor / VS Code (notebook):**

1. Abra a pasta **`recfair/`** como workspace.
2. O interpretador padrão aponta para `venv-recfair/bin/python` (`.vscode/settings.json`).
3. No notebook, kernel **Python (recfair)**.

Se `venv-recfair/` não existir: `make install-dev && make kernel`.

## Experimentos (E1 baseline)

| Experimento | Comando |
| :--- | :--- |
| Chat interativo (baseline) | `make chat ARCH=baseline` |
| Golden-set completo (30 casos) | notebook [`eval/notebooks/E1_baseline_report.ipynb`](eval/notebooks/E1_baseline_report.ipynb) |
| Regenerar CSVs sintéticos | `make data` |

O relatório Jupyter importa `recfair.*` e `eval.*` — células de código **não** implementam o sistema.

## Layout

- `recfair/` — runtime (CLI, grafos, schemas, catálogo)
- `eval/` — medição (`run_eval`, verify, report) + `notebooks/` + `runs/`
- `data/golden/cases.json` — golden-set congelado (hash `golden_revision`)

## Arquitetura vigente

E1: `baseline` — uma chamada LLM com stuffing de catálogo + vendas (`prompt_version=v1`).
