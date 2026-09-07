# Especificação do Makefile

Na raiz do `pyproject.toml`. `.PHONY` em todos os alvos. Primeiro alvo: `help`.

`PKG` = pacote Python. `ARCH` default = id da arquitetura **vigente** (não o baseline).

```makefile
.PHONY: help install install-dev lock lint format typecheck test eval chat ingest mcp

PKG ?= my_package
ARCH ?= current
POETRY ?= poetry

help:
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

install: ## runtime deps
	$(POETRY) install --only main

install-dev: ## runtime + grupos dev, eval, ui
	$(POETRY) install --with dev,eval,ui

lock: ## refresh poetry.lock
	$(POETRY) lock

lint: ## ruff check
	$(POETRY) run ruff check src tests

format: ## ruff format
	$(POETRY) run ruff format src tests

typecheck: ## mypy
	$(POETRY) run mypy src

test: ## pytest
	$(POETRY) run pytest -q

eval: ## golden-set; ARCH=baseline|current|<id>
	$(POETRY) run python -m $(PKG).eval.runner --arch $(ARCH)

chat: ## terminal UI (default = vigente)
	$(POETRY) run python -m $(PKG).cli --arch $(ARCH)

ingest: ## vector index (se RAG existir)
	$(POETRY) run python -m $(PKG).rag.ingest

mcp: ## MCP server (se existir)
	$(POETRY) run python -m $(PKG).mcp.server
```

`ARCH=current` resolve no código para o id vigente. `ingest`/`mcp` inexistentes: mensagem “peça não habilitada”, não ImportError opaco.

README mínimo:

```bash
cp .env.example .env
make install-dev
make chat
make chat ARCH=baseline
make eval ARCH=baseline
make eval
```
