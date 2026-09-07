# Toolkit de IA para desenvolvimento (Cursor)

Este arquivo é o **índice e o contrato** do toolkit versionado em `.cursor/`. Serve a dois leitores:

| Quem | Como usar |
| :--- | :--- |
| **Agente de IA** | Trate as seções *Contrato* e *Como aplicar* como obrigatórias. Antes de implementar, **leia a skill** da tabela *Roteiro*. Delegue o subagent quando a tarefa for review/especialista. |
| **Dev humano** | Use como mapa do que existe, quando dispara, e onde está o detalhe. As instruções longas estão nas skills, não aqui. |

Nada neste toolkit é código da aplicação. O software (quando existir) vive no diretório do `pyproject.toml` (`src/`, CLI, `docs/`, `eval/`). Este repositório também pode conter material de curso fora desse pacote — **não misture** os dois.

---

## Peças do toolkit (o que é cada uma)

```
AGENTS.md                 ← você está aqui (contrato + índice)
.cursor/rules/*.mdc       ← contexto injetado automaticamente
.cursor/skills/<nome>/    ← playbooks: o agente lê quando a tarefa combina
.cursor/agents/*.md       ← subagents: contexto isolado, invocados sob demanda
```

| Peça | Papel | Quem dispara |
| :--- | :--- | :--- |
| **Rule** (`.mdc`) | Restrição curta e permanente | Cursor: `alwaysApply` em toda conversa, ou `globs` quando arquivos batem |
| **Skill** (`SKILL.md` + anexos) | Procedimento e templates | Agente: pela `description` da skill, ou quando este arquivo manda ler |
| **Subagent** (`.cursor/agents/*.md`) | Especialista em contexto separado | Agente principal: *use proactively* na description, ou o humano pede pelo nome |

Não edite uma rule para caber um playbook inteiro — isso é skill. Não copie o domínio do projeto (métricas, dataset) para este toolkit: cada produto define isso em `data/` e `src/<package>/eval/`.

---

## Contrato (obrigatório)

### Idioma

- Conversar e documentar em **português**.
- Identificadores, módulos, commits e comentários de código em **inglês**.
- Docstrings em inglês (Google style). ADRs e `docs/` em português.

### Sistema vs notebook

- O **sistema** é um pacote Python **CLI** (Poetry, Makefile, `src/`). Harness, grafos, tools, memória, verify e métricas **não** vivem em notebook.
- Notebooks são **documentação** (Markdown da entrega) e **relatório**: importam o pacote e chamam funções/CLI. Célula não implementa agente, tool, grafo nem métrica.
- Python **3.14**, dependências com **Poetry** (`pyproject.toml` + `poetry.lock` commitado).
- Sem chaves de API em git, notebook, código ou prompt versionado. Só `.env` (ignorado) e `.env.example`.
- Efeitos irreversíveis: humano no loop.

### Evolução de arquitetura

- Comece pelo baseline mais simples que resolve a tarefa.
- Prompt, tools, RAG, MCP, grafos (LangGraph) e multiagente são **peças sem ordem fixa**.
- O **default do CLI** (`make chat`, `make eval`) é a arquitetura do **incremento vigente**. Baseline sempre executável: `ARCH=baseline`.
- Empate ou piora no eval é resultado **válido** (relatar com hipótese). Não apaga a versão vigente. Peças **além** do incremento só entram com limitação medida.
- Cada arquitetura: `id` + **data** (ISO) + ADR. Comparar versões: **mesmo modelo**, mesmo ambiente, baseline **reexecutado** na mesma sessão.

### Golden-set

- Só **cresce** (tamanho e escopo). Casos antigos não se apagam nem se reescrevem.
- Exceção: **defeito real** (formulação, rótulo, verificação que não mede o pretendido). Registrar o que mudou; reexecutar baseline e versão atual.
- Hash (`golden_revision`) em cada run.
- Na comparação principal: funções de verificação, critérios de sucesso e formato de saída da régua original **não mudam**.

### Instrumentação de run

Toda execução reportada registra: modelo+versão, temperatura, data, versão do prompt, `architecture_id`, latência, nº de chamadas LLM e tools, tokens in/out, custo estimado, `halt_reason` se houver.

---

## Rules — `.cursor/rules/`

Injeção automática. O agente **não precisa abrir** o arquivo para elas valerem; este índice existe para o humano e para saber *quando* cada uma entra.

| Arquivo | Disparo | Função |
| :--- | :--- | :--- |
| [`multi-agent-core.mdc`](.cursor/rules/multi-agent-core.mdc) | **Sempre** (`alwaysApply`) | Espelho curto deste contrato: CLI vs notebook, evolução, golden-set, Poetry 3.14, idioma, lista de skills |
| [`python-standards.mdc`](.cursor/rules/python-standards.mdc) | `src/**/*.py`, `tests/**/*.py` | PEP 8, tipos, SOLID, nós puros, tools com schema, sem lógica em notebook |
| [`eval-notebooks.mdc`](.cursor/rules/eval-notebooks.mdc) | `eval/**/*.ipynb`, `**/notebooks/**/*.ipynb`, `**/*eval*.ipynb`, `E*.ipynb` | Notebook = relatório; estrutura herdada por import; mesmo modelo; hash do golden-set |
| [`architecture-docs.mdc`](.cursor/rules/architecture-docs.mdc) | `docs/**/*.md` | ADR datado em mudança de arquitetura; `docs/architecture.md` = desenho **atual** |

Se criar uma rule nova, acrescente a linha nesta tabela no mesmo PR.

---

## Skills — `.cursor/skills/<nome>/`

Playbooks. **Leia o `SKILL.md` (e o anexo citado) antes de implementar** a tarefa correspondente. Anexos são referência sob demanda (progressive disclosure).

### `multi-agent-patterns`

Arquitetura, harness, tools, RAG, MCP, LangGraph, memória.

| Arquivo | Conteúdo |
| :--- | :--- |
| [`SKILL.md`](.cursor/skills/multi-agent-patterns/SKILL.md) | Postura (Model + Harness), evolução, catálogo de peças, padrões de grafo, memória, checklist |
| [`gates.md`](.cursor/skills/multi-agent-patterns/gates.md) | Quando considerar cada peça; tools reais; MCP opcional; hard-stops |
| [`langgraph.md`](.cursor/skills/multi-agent-patterns/langgraph.md) | State, módulos por `architecture_id`, nós, `recursion_limit`, `thread_id` |

### `python-agent-quality`

Qualidade do código Python do pacote.

| Arquivo | Conteúdo |
| :--- | :--- |
| [`SKILL.md`](.cursor/skills/python-agent-quality/SKILL.md) | Python 3.14, mapa de módulos, SOLID, refactor, erros, testes; notebook não é módulo |
| [`STANDARDS.md`](.cursor/skills/python-agent-quality/STANDARDS.md) | Exemplos: port/adapter, schema de tool, docstring Google, anti-padrão |

### `agent-evaluation`

Golden-set, runner no pacote, comparação, notebooks que só invocam.

| Arquivo | Conteúdo |
| :--- | :--- |
| [`SKILL.md`](.cursor/skills/agent-evaluation/SKILL.md) | Regras do conjunto, mesmo modelo, instrumentação, eixos de comparação (não fórmulas), modos de falha, ganho/empate/piora |
| [`notebook-template.md`](.cursor/skills/agent-evaluation/notebook-template.md) | Ordem das células do relatório e o que é proibido nelas |

**Não** define métricas nem o schema dos casos — isso é do projeto.

### `project-ops`

Esqueleto, Poetry, Makefile, CLI, README de experimentos.

| Arquivo | Conteúdo |
| :--- | :--- |
| [`SKILL.md`](.cursor/skills/project-ops/SKILL.md) | Fonte da verdade, grupos de deps, UI Rich, checklist de bootstrap |
| [`layout.md`](.cursor/skills/project-ops/layout.md) | Árvore canônica `src/<package>/`, `data/golden/`, `eval/`, `docs/adr/` |
| [`makefile-spec.md`](.cursor/skills/project-ops/makefile-spec.md) | Alvos `install`, `install-dev`, `lock`, `lint`, `test`, `eval`, `chat`, `ingest`, `mcp` |

### `architecture-adrs`

Decisões técnicas datadas e mapa de arquitetura.

| Arquivo | Conteúdo |
| :--- | :--- |
| [`SKILL.md`](.cursor/skills/architecture-adrs/SKILL.md) | Quando gravar ADR, conteúdo mínimo, o que vai em `docs/architecture.md` |
| [`adr-template.md`](.cursor/skills/architecture-adrs/adr-template.md) | Modelo do arquivo `docs/adr/NNNN-slug.md` |

---

## Subagents — `.cursor/agents/`

Contexto isolado. O agente principal **deve delegar** nestes gatilhos (e o humano pode pedir: *use o subagent X para …*).

| Nome | Arquivo | Delegar quando |
| :--- | :--- | :--- |
| `architecture-guardian` | [`architecture-guardian.md`](.cursor/agents/architecture-guardian.md) | Novo agente, tool, RAG, MCP, grafo, memória; promoção; review se a peça extra tem evidência; recusar lógica de sistema em notebook |
| `eval-engineer` | [`eval-engineer.md`](.cursor/agents/eval-engineer.md) | Criar/alterar golden-set, runner, notebook de relatório; interpretar comparação; não inventar métricas |
| `python-quality` | [`python-quality.md`](.cursor/agents/python-quality.md) | Depois de escrever ou alterar `.py`: PEP, SOLID, testes; 🔴 se o sistema estiver no notebook |

Feedback do `python-quality`: 🔴 critical · 🟡 should fix · 🟢 nice.

---

## Como aplicar (roteiro)

O agente segue esta tabela **antes** de gerar código. O humano usa a mesma tabela para saber o que pedir.

| Tarefa | Ler | Delegar |
| :--- | :--- | :--- |
| Criar esqueleto, deps, Makefile, CLI, README | `project-ops` (+ `layout.md`, `makefile-spec.md`) | — |
| Baseline, tools, RAG, MCP, grafo, memória, harness | `multi-agent-patterns` (+ `gates.md`; `langgraph.md` se houver grafo) | `architecture-guardian` |
| ADR / mapa `docs/architecture.md` | `architecture-adrs` (+ `adr-template.md`) | `architecture-guardian` |
| Escrever ou refatorar Python | `python-agent-quality` (+ `STANDARDS.md`) | `python-quality` (depois) |
| Golden-set, runner, comparação, notebook de entrega | `agent-evaluation` (+ `notebook-template.md`) | `eval-engineer` |
| Editar `docs/**/*.md` | rule `architecture-docs` já vale; skill `architecture-adrs` se for decisão | — |
| Editar `*.ipynb` de eval/entrega | rule `eval-notebooks` já vale; skill `agent-evaluation` | `eval-engineer` |

**Ordem típica de um incremento:** `architecture-guardian` (desenho mínimo) → implementação com `project-ops` + `python-agent-quality` → `python-quality` no diff → `eval-engineer` (runner + relatório) → ADR datado.

### Invocação explícita (humano)

```
Use o architecture-guardian para revisar se cabe um supervisor.
Use o eval-engineer para acrescentar casos e reexecutar o baseline.
Use o python-quality neste diff.
Siga a skill project-ops e crie o esqueleto Poetry.
```

---

## CLI de referência (quando o app existir)

Detalhe normativo: skill `project-ops`. Resumo:

| Comando | Efeito |
| :--- | :--- |
| `make install` / `make install-dev` | Poetry (runtime / + dev,eval,ui) |
| `make chat` | UI no terminal — **arquitetura vigente** |
| `make chat ARCH=baseline` | Mesma UI, baseline |
| `make eval` | Golden-set na vigente |
| `make eval ARCH=baseline` | Golden-set no baseline (obrigatório em toda comparação) |
| `make lint` `make test` | Qualidade |
| `make ingest` / `make mcp` | Só se a peça existir |

O README do app mapeia **cada experimento do notebook** para um desses comandos (entrega CLI / zip).

---

## Inventário (manter sincronizado)

Qualquer arquivo novo em `.cursor/rules`, `.cursor/skills` ou `.cursor/agents` **entra neste inventário no mesmo PR**.

```
.cursor/rules/
  multi-agent-core.mdc
  python-standards.mdc
  eval-notebooks.mdc
  architecture-docs.mdc
.cursor/skills/
  multi-agent-patterns/   SKILL.md  gates.md  langgraph.md
  python-agent-quality/   SKILL.md  STANDARDS.md
  agent-evaluation/       SKILL.md  notebook-template.md
  project-ops/            SKILL.md  layout.md  makefile-spec.md
  architecture-adrs/      SKILL.md  adr-template.md
.cursor/agents/
  architecture-guardian.md
  eval-engineer.md
  python-quality.md
```

4 rules · 5 skills · 3 subagents.
