.PHONY: help install install-dev kernel lint format chat data

ARCH ?= current
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

# Export .env into the recipe shell (HF_TOKEN, GOOGLE_API_KEY). Python also
# loads .env via recfair.config.apply_dotenv; this covers HuggingFace Hub
# before the interpreter starts. Quotes in .env are handled by the shell.
DOTENV = set -a; [ -f .env ] && . ./.env; set +a

lint: ## ruff check
	$(PYTHON) -m ruff check recfair eval tests

format: ## ruff format
	$(PYTHON) -m ruff format recfair eval tests

data: ## regenerate CSVs and FAISS indexes (claims + FAQ)
	$(DOTENV); $(PYTHON) -m recfair.data.catalog
	$(DOTENV); $(PYTHON) -m recfair.rag.indexes

chat: ## terminal UI (default = vigente via ARCH=current)
	$(DOTENV); $(PYTHON) -m recfair.cli --arch $(ARCH)
