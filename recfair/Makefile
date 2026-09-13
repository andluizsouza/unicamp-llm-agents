.PHONY: help install install-dev kernel lint format chat data

ARCH ?= baseline
VENV ?= venv-recfair
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help: ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

install: ## runtime deps + editable package
	@test -d $(VENV) || python3.14 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

install-dev: ## runtime + dev, notebooks, UI + editable package
	@test -d $(VENV) || python3.14 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .

kernel: install-dev ## register Jupyter kernel for notebooks
	$(PYTHON) -m ipykernel install --user --name recfair --display-name "Python (recfair)"

lint: ## ruff check
	$(PYTHON) -m ruff check recfair eval

format: ## ruff format
	$(PYTHON) -m ruff format recfair eval

data: ## regenerate CSVs from catalog module
	$(PYTHON) -m recfair.data.catalog

chat: ## terminal UI (default arch = baseline / current)
	$(PYTHON) -m recfair.cli --arch $(ARCH)
