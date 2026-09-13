# Layout canônico

`<app>/` é o diretório do `requirements.txt`. O runtime vive no pacote `<package>/` na raiz do app (sem `src/` obrigatório). A medição vive no pacote `eval/` na mesma raiz.

```
<app>/
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml          # setuptools + ruff
├── Makefile
├── langgraph.json          # só se houver grafo deployável
├── .python-version         # 3.14
├── .env.example
├── .vscode/settings.json   # interpretador: ${workspaceFolder}/venv-<app>/bin/python
├── README.md               # instalar + experimento → comando ou notebook
├── docs/
│   ├── INSTALL.md          # guia venv + pip
│   ├── architecture.md
│   └── adr/
├── <package>/              # runtime — import <package>.*
│   ├── __init__.py
│   ├── config.py
│   ├── logging.py
│   ├── cli.py              # python -m <package>.cli
│   ├── schemas/            # formato de saída estável entre versões
│   ├── prompts/
│   ├── tools/              # quando existir
│   ├── rag/                # quando existir
│   ├── mcp/                # quando existir
│   ├── graphs/             # um módulo por architecture_id + registry.py
│   ├── agents/             # quando existir
│   ├── observability/
│   └── data/               # loaders de dataset (CSV, SQLite)
├── eval/                   # medição — import eval.*
│   ├── __init__.py
│   ├── runner.py           # run_eval() — chamado pelo notebook
│   ├── verify.py
│   ├── gold.py
│   ├── fingerprint.py
│   ├── report.py
│   ├── notebooks/          # relatório (Markdown + chamadas)
│   └── runs/               # JSON por execução
└── data/
    └── golden/
```

Pacote editável via `pip install -e .` (setuptools em `pyproject.toml`).

Pastas de peças ainda não usadas **não** precisam existir. Sem `tests/`, `scripts/` nem pacote `harness/` separado — registry de arquiteturas em `graphs/registry.py`.

Índices vetoriais locais no `.gitignore`; alvo `ingest` só quando RAG existir (não é obrigatório no Makefile mínimo).
