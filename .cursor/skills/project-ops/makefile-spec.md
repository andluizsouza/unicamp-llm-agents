# Especificação do Makefile

Na raiz do `requirements.txt`. `.PHONY` em todos os alvos. Primeiro alvo: `help`.

`PKG` = pacote Python. `ARCH` default = id da arquitetura **vigente** (não o baseline). `VENV` = nome do ambiente virtual (ex. `venv-<app>`).

```makefile
.PHONY: help install install-dev kernel lint format chat data

PKG ?= my_package
ARCH ?= current
VENV ?= venv-myapp
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help:
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

install: ## runtime deps + editable package
	@test -d $(VENV) || python3.14 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

install-dev: ## runtime + dev, notebooks, ui + editable package
	@test -d $(VENV) || python3.14 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .

kernel: install-dev ## Jupyter kernel for notebooks
	$(PYTHON) -m ipykernel install --user --name $(PKG) --display-name "Python ($(PKG))"

lint: ## ruff check
	$(PYTHON) -m ruff check <package> eval

format: ## ruff format
	$(PYTHON) -m ruff format <package> eval

data: ## regenerate local datasets (if applicable)
	$(PYTHON) -m <package>.data.catalog

chat: ## terminal UI (default = vigente)
	$(PYTHON) -m $(PKG).cli --arch $(ARCH)
```

`ARCH=current` resolve no código para o id vigente. Golden-set: notebook chama `eval.runner.run_eval` — **sem** alvo `make eval`. Interpretador IDE: `.vscode/settings.json` com `${workspaceFolder}/venv-<app>/bin/python`.

README mínimo:

```bash
python3.14 -m venv venv-<app>
source venv-<app>/bin/activate
cp .env.example .env
make install-dev
make kernel
make chat
make chat ARCH=baseline
```

Resultados do golden-set: notebook `eval/notebooks/…` executa `run_eval`.
