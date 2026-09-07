---
name: project-ops
description: >-
  Define layout do pacote Python, Poetry, Makefile, CLI de experimentos e
  notebooks que só invocam o pacote. Use ao criar o esqueleto, dependências,
  README de execução ou UI no terminal.
---

# Operação do projeto

O produto é um **sistema CLI**. O notebook da entrega documenta e chama esse sistema; o zip de código-fonte deve permitir reproduzir cada experimento do relatório por linha de comando.

## Fonte da verdade

| Artefato | Papel |
| :--- | :--- |
| `pyproject.toml` | Metadados, deps, grupos Poetry, ruff/mypy/pytest |
| `poetry.lock` | Pin reproduzível (**commitar**) |
| `.python-version` | `3.14` |
| `.env.example` | Nomes de variáveis, sem segredos |
| `Makefile` | Interface humana/CI |
| `README.md` | Como instalar e **tabela experimento → comando** |

Gerenciador: **Poetry**. Python **3.14**. Sem `requirements.txt` paralelo. Sem commitar `.venv` nem `.env`.

Raiz do app = diretório do `pyproject.toml`.

## Layout

Detalhe: [layout.md](layout.md).

## Dependências

- Pin no `poetry.lock`. Bounds razoáveis; mais estreitos em clientes de LLM e orquestradores.
- Grupos: `dev` (ruff, mypy, pytest), `eval` (jupyter, pandas, matplotlib), `ui` (rich).
- Instale o que a arquitetura **vigente** usa. Framework novo que mude arquitetura → linha no ADR.
- Se uma dependência externa não puder ser instalada no ambiente de correção, **mocke** e documente no README.
- Modelos e versões de runtime entram no relatório de eval.

## Makefile e CLI

Alvos: [makefile-spec.md](makefile-spec.md).

| Alvo | Faz |
| :--- | :--- |
| `make install` | `poetry install --only main` |
| `make install-dev` | `poetry install --with dev,eval,ui` |
| `make lock` | `poetry lock` |
| `make lint` / `format` / `typecheck` / `test` | qualidade |
| `make chat` | UI no terminal — **default = arquitetura vigente** |
| `make eval` | golden-set; `ARCH=baseline` ou vigente |
| `make ingest` / `make mcp` | se a peça existir; senão mensagem clara |

`make chat ARCH=baseline` (e o mesmo em `eval`) mantém a v1 executável.

## README de experimentos

O README mapeia **cada experimento** que o notebook relata para um comando, por exemplo:

```text
make install-dev
make chat                          # versão vigente
make chat ARCH=baseline
make eval ARCH=baseline
make eval ARCH=<id-vigente>
```

Quem recebe só o zip deve conseguir reproduzir o relatório sem abrir o Jupyter, salvo a redação em Markdown.

## UI local (`make chat`)

Rich (console + prompt). Entry: `poetry run python -m <package>.cli`.

Mostrar: turno, tools (nome+args), saída estruturada, latência, `halt_reason` se houver.

Comandos: `/quit`, `/reset`, `/trace`, `/arch <id>`.

Sem API keys na tela. Falhar cedo se env obrigatória faltar.

## Checklist ao bootstrapar

```
- [ ] pyproject.toml (requires-python >=3.14) + poetry.lock + Makefile
- [ ] README com tabela experimento → comando
- [ ] CLI default = incremento vigente; baseline via ARCH
- [ ] .env.example; .gitignore: .venv, .env
```
