# Guia de instalação — RecFair

Este projeto usa **Python 3.14** nativo com `venv` e `pip`. Não é necessário Poetry.

## Pré-requisitos

- Python **3.14** instalado (`python3.14 --version`)
- `make` (opcional, mas recomendado — os alvos encapsulam os comandos abaixo)

## 1. Clonar e entrar no app

```bash
cd recfair
```

## 2. Criar e ativar o ambiente virtual

```bash
python3.14 -m venv venv-recfair
source venv-recfair/bin/activate
```

No Windows (PowerShell):

```powershell
python3.14 -m venv venv-recfair
.\venv-recfair\Scripts\Activate.ps1
```

## 3. Instalar dependências

**Desenvolvimento completo** (runtime + notebooks + UI):

```bash
make install-dev
```

Equivalente manual:

```bash
pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -e .
```

**Somente runtime** (CLI, sem Jupyter):

```bash
make install
```

Equivalente manual:

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

O `pip install -e .` registra os pacotes `recfair` e `eval` em modo editável.

## 4. Variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` e defina:

| Variável | Uso |
| :--- | :--- |
| `GOOGLE_API_KEY` (ou `GEMINI_API_KEY`) | Gemini — `make chat` e `run_eval` no notebook |
| `HF_TOKEN` | Hugging Face Hub — download autenticado do MiniLM (`make data`, FAQ RAG, claims semânticos) |

O runtime **exporta** essas variáveis de duas formas (nenhuma imprime o valor):

1. **Makefile** (`make data`, `make chat`) — `set -a; . ./.env` no shell da receita.
2. **Python** — `recfair.config.apply_dotenv()` lê o `.env` e `export_hf_token()` replica `HF_TOKEN` em `HUGGING_FACE_HUB_TOKEN` (o que o Hub espera). `SentenceTransformer` e `HuggingFaceEmbeddings` recebem `token=` na construção do modelo.

Token Hugging Face: [settings/tokens](https://huggingface.co/settings/tokens) (escopo de leitura basta). Não commitar `.env`.

## 5. Cursor / VS Code e notebooks

```bash
make kernel
```

Isso registra o kernel Jupyter **Python (recfair)**. O interpretador padrão está em `.vscode/settings.json` (`venv-recfair/bin/python`).

Depois:

1. Abra a pasta `recfair/` como workspace.
2. **Developer: Reload Window** no Command Palette (se necessário).
3. No notebook, selecione o kernel **Python (recfair)**.

## 6. Verificar instalação

```bash
make data                 # CSVs + índices FAISS — requer HF_TOKEN
make chat                 # vigente = multiagent — requer GOOGLE_API_KEY
make chat ARCH=workflow   # E2
make chat ARCH=baseline   # E1
```

Mapa do repositório: [`README.md`](../README.md). Arquitetura: [`docs/architecture.md`](architecture.md).

Relatórios de eval: [`eval/notebooks/E1_baseline.ipynb`](../eval/notebooks/E1_baseline.ipynb) · [`eval/notebooks/E2_workflow.ipynb`](../eval/notebooks/E2_workflow.ipynb) · [`eval/notebooks/E3_evaluation.ipynb`](../eval/notebooks/E3_evaluation.ipynb).

Sem `GOOGLE_API_KEY` o `run_eval` do notebook não roda. Sem `HF_TOKEN` o `make data` falha ao baixar o MiniLM. `pytest` e `make lint` cobrem régua, guardrails e contratos sem chaves.

## Arquivos de dependências

| Arquivo | Conteúdo |
| :--- | :--- |
| `requirements.txt` | Runtime: langchain, langgraph, sentence-transformers, faiss-cpu, pandas, pydantic, rich |
| `requirements-dev.txt` | Inclui runtime + ruff, jupyter, ipykernel, pytest |

Bounds versionados nos arquivos; para pin exato de todas as transitivas, use `pip freeze > requirements.lock` localmente (não versionado por padrão).

## Solução de problemas

| Sintoma | Ação |
| :--- | :--- |
| `python3.14: command not found` | Instale Python 3.14 ou ajuste o comando para o binário disponível no sistema |
| `make: python3.14: No such file` | Crie o venv manualmente com o binário correto e use `VENV=venv-recfair make install-dev` |
| Notebook sem kernel | `make install-dev && make kernel`, depois recarregue a janela |
| `ModuleNotFoundError: recfair` | Ative o venv e rode `pip install -e .` |
| FAQ/claims falham com `Missing … index` | Rode `make data` (gera FAISS em `data/indexes/`, gitignored) |
| 401 / gated Hugging Face ao baixar MiniLM | Defina `HF_TOKEN` em `.env` e rode de novo `make data` (o Makefile exporta o token) |
