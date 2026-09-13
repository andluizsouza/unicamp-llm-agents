---
name: project-ops
description: >-
  Define layout do pacote Python, venv/pip, Makefile, CLI de experimentos e
  notebooks que só invocam o pacote. Use ao criar o esqueleto, dependências,
  README de execução ou UI no terminal.
---

# Operação do projeto

O produto é um **sistema CLI** (`make chat`). O notebook da entrega documenta, executa o golden-set e apresenta resultados; o zip de código-fonte deve permitir reproduzir cada experimento.

## Fonte da verdade

| Artefato | Papel |
| :--- | :--- |
| `requirements.txt` | Dependências de runtime |
| `requirements-dev.txt` | Runtime + dev, notebooks, ui (`-r requirements.txt`) |
| `pyproject.toml` | Metadados do pacote (setuptools), ruff |
| `.python-version` | `3.14` |
| `.env.example` | Nomes de variáveis, sem segredos |
| `Makefile` | Interface humana |
| `README.md` | Como instalar e **tabela experimento → comando ou notebook** |
| `docs/INSTALL.md` | Guia detalhado de venv + pip |

Gerenciador: **pip** em **venv** (`python3.14 -m venv venv-<app>`). Python **3.14**. Sem commitar `venv-<app>/` nem `.env`.

Raiz do app = diretório do `requirements.txt`.

## Layout

Detalhe: [layout.md](layout.md).

## Dependências

- Bounds em `requirements.txt` / `requirements-dev.txt`; mais estreitos em clientes de LLM e orquestradores.
- Grupos: runtime (`requirements.txt`); dev/notebooks/ui em `requirements-dev.txt`.
- Instale o que a arquitetura **vigente** usa. Framework novo que mude arquitetura → linha no ADR.
- Se uma dependência externa não puder ser instalada no ambiente de correção, **mocke** e documente no README.
- Modelos e versões de runtime entram no relatório de eval.

## Makefile e CLI

Alvos: [makefile-spec.md](makefile-spec.md).

| Alvo | Faz |
| :--- | :--- |
| `make install` | `pip install -r requirements.txt` + `pip install -e .` |
| `make install-dev` | `pip install -r requirements-dev.txt` + `pip install -e .` |
| `make kernel` | kernel Jupyter para notebooks |
| `make lint` / `format` | ruff |
| `make chat` | UI no terminal — **default = arquitetura vigente** |
| Golden-set | notebook chama `eval.runner.run_eval` (sem `make eval`) |

`make chat ARCH=baseline` mantém a v1 executável.

## README de experimentos

O README mapeia **cada experimento** que o notebook relata, por exemplo:

```text
python3.14 -m venv venv-<app>
source venv-<app>/bin/activate
make install-dev
make kernel
make chat                          # versão vigente
make chat ARCH=baseline
# golden-set: eval/notebooks/<relatório>.ipynb → run_eval(arch="baseline")
```

Quem recebe o zip reproduz o chat por CLI e o golden-set pelo notebook.

## UI local (`make chat`)

Rich (console + prompt). Entry: `python -m <package>.cli` (com venv ativo).

Mostrar: turno, tools (nome+args), saída estruturada, latência, `halt_reason` se houver.

Comandos: `/quit`, `/reset`, `/trace`, `/arch <id>`.

Sem API keys na tela. Falhar cedo se env obrigatória faltar.

## Checklist ao bootstrapar

```
- [ ] requirements.txt + requirements-dev.txt + pyproject.toml (setuptools) + Makefile
- [ ] README com tabela experimento → comando/notebook + docs/INSTALL.md
- [ ] CLI default = incremento vigente; baseline via ARCH
- [ ] .vscode/settings.json com interpretador relativo ao workspace
- [ ] .env.example; .gitignore: venv-<app>/, .env
```
