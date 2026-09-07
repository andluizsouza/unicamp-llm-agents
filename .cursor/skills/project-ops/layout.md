# Layout canônico

`<app>/` é o diretório do `pyproject.toml`. `<package>` é o nome em `src/`.

```
<app>/
├── pyproject.toml
├── poetry.lock
├── Makefile
├── langgraph.json          # só se houver grafo deployável
├── .python-version         # 3.14
├── .env.example
├── README.md               # instalar + experimento → comando
├── src/<package>/
│   ├── __init__.py
│   ├── config.py
│   ├── logging.py
│   ├── cli.py              # python -m <package>.cli
│   ├── schemas/            # formato de saída estável entre versões
│   ├── prompts/
│   ├── tools/
│   ├── rag/
│   ├── mcp/
│   ├── graphs/             # um módulo por architecture_id, baseline intacto
│   ├── agents/
│   ├── harness/
│   ├── observability/
│   └── eval/               # runner e verify — importados pelo notebook
│       ├── runner.py
│       └── fingerprint.py  # hash do golden-set
├── data/
│   └── golden/
├── eval/
│   ├── runs/
│   └── notebooks/          # só relatório (Markdown + chamadas)
├── docs/
│   ├── architecture.md
│   └── adr/
└── tests/
```

Pacote editável via Poetry.

Pastas de peças ainda não usadas **não** precisam existir.

Índices vetoriais locais no `.gitignore`; `make ingest` reconstrói quando RAG existir.
