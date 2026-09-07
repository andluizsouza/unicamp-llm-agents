---
name: python-agent-quality
description: >-
  Aplica PEP 8/257, type hints, Google docstrings, SOLID, modularização e
  refactor em código Python de sistemas multiagente (agentes, tools, grafos,
  RAG, MCP, eval, CLI). Use ao escrever, revisar ou refatorar arquivos .py.
---

# Qualidade Python para agentes

## Defaults

- Python **3.14**, Ruff (lint+format), `mypy` estrito nas APIs públicas.
- Type hints em funções públicas. Pydantic v2 para I/O e configs.
- Docstrings **Google style** em inglês em módulos, classes e funções públicas. Comentários só para *porquê*.

## Mapa de módulos (não misturar)

| Pacote | Pode | Não pode |
| :--- | :--- | :--- |
| `schemas/` | Contratos Pydantic | Chamar LLM |
| `prompts/` | Templates versionados | Lógica de negócio |
| `tools/` | Adapters de ação | Orquestrar o grafo |
| `rag/` | Ingestão/retrieval | Gerar a resposta final |
| `mcp/` | Server MCP | Estado de sessão |
| `graphs/` | Compilar StateGraph | SQL/HTTP direto |
| `agents/` | Personas/prompts de especialista | Duplicar tools |
| `harness/` | constrain/verify/correct | Prompt do produto |
| `eval/` | Runner e medição | Mutar produção |
| `cli/` | TUI/REPL | Política de domínio |

Nova arquitetura = novo módulo. Não inchar `graph.py`. Baseline permanece importável.

**Notebooks não são módulos.** Se a lógica está numa célula, extraia para `src/` e a célula só chama.

## SOLID

- **S:** um agente/tool/nó = um motivo para mudar.
- **O:** versão nova de arquitetura em módulo novo + ADR datado.
- **L:** ports (`Protocol`) honrados por qualquer adapter (LLM, retriever, store).
- **I:** tools pequenas e específicas — não um `do(action, **kwargs)`.
- **D:** nós dependem de ports; o composition root injeta implementações.

## Refactor — faça quando

- Arquivo > ~250 linhas com duas razões de mudança
- Cópia de prompt ou schema entre versões
- Nó com HTTP/SQL/embedding inline
- Teste que precisa de API real para validar schema

Receita: extrair port → adapter → teste de unidade no adapter → nó só orquestra.

## Funções e erros

- Nomes: verbos para nós/tools.
- Retorno de nó: `dict` parcial do state, sem mutar o objeto recebido.
- Exceções de domínio na borda (harness/correct). Nada de `except Exception: pass`.
- Tool devolve `{ok: false, error: ...}` para o modelo corrigir.

## Testes

- Unit: schemas, verify, adapters.
- Graph: LLM/retriever fake (`Protocol` + stub).
- Qualidade da solução: golden-set via runner no pacote — skill `agent-evaluation`. O notebook só chama esse runner.

Exemplos: [STANDARDS.md](STANDARDS.md).
