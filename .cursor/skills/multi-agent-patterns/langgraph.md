# LangGraph (quando o projeto tiver grafo)

## Estado

Contrato único (`TypedDict` ou modelo Pydantic) + reducers. Listas que acumulam usam `add` / `add_messages`; campos “atuais” sobrescrevem.

Mantenha o state enxuto: entrada da tarefa, artefatos intermediários necessários aos próximos nós, erros, `step`, `halt_reason`. Sem dump de resposta bruta do LLM. Sem dados que a política do projeto proíba persistir.

Exemplo mínimo:

```python
from typing import Annotated, TypedDict
from operator import add

class GraphState(TypedDict):
    input: str
    messages: Annotated[list, add]
    artifacts: dict
    errors: Annotated[list[str], add]
    step: int
    halt_reason: str | None
```

Campos de domínio entram neste contrato pelo projeto, não por esta skill.

## Módulos

```
src/<package>/graphs/
  state.py
  compile.py          # factory: architecture_id -> compiled graph
  <architecture_id>.py
```

Cada arquivo de arquitetura expõe `build_graph()`. `compile.py` é o único importado pela CLI. Baseline e versões anteriores continuam compiláveis (`--arch`).

O default da CLI é a arquitetura do **incremento vigente**, não necessariamente a de melhor eval.

## Nó

`(state: GraphState) -> dict`. Não mutar `state`. I/O via port injetada.

Aresta condicional: `Literal[...]` validado. Após `Send()` paralelo, um join valida campos obrigatórios.

## Observabilidade

Incrementar `step`. Se `step >= MAX` ou custo excedido → `halt_reason` (ex.: `recursion_limit`) e `END`. Registrar como modo de falha na eval.

`thread_id` estável na CLI (isolamento de sessões). Checkpointer em memória no `make chat`; persistência em disco só com ADR datado.
