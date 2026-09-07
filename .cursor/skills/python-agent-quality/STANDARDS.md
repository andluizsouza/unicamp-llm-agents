# Padrões Python (exemplos)

## Port + adapter

```python
from typing import Protocol

class RecordStore(Protocol):
    def get(self, record_id: str) -> dict: ...

class CsvRecordStore:
    """Store backed by a local CSV snapshot."""

    def __init__(self, path: str) -> None: ...
    def get(self, record_id: str) -> dict: ...
```

O nó recebe `RecordStore`, nunca `pandas.read_csv` inline.

## Tool com schema e erro estruturado

```python
from pydantic import BaseModel, Field

class LookupArgs(BaseModel):
    record_id: str = Field(description="Stable id, e.g. rec_1042")

class LookupResult(BaseModel):
    ok: bool
    record_id: str
    payload: dict | None = None
    error: str | None = None
```

Descrição da tool: *quando* usar e *o que não* usar (“não inventar id; se ausente, ok=false”).

## Docstring Google

```python
def merge_artifacts(parts: list[dict], key: str) -> dict:
    """Merge ordered artifact dicts by ``key``.

    Args:
        parts: Partial results from upstream nodes.
        key: Field that identifies each item.

    Returns:
        Combined map keyed by ``key``.
    """
```

## O que recusar em review

```python
# BAD: nó orquestra + HTTP + prompt + parse
def node(state):
    r = requests.get(os.environ["URL"], params=state)
    text = ChatOpenAI().invoke(PROMPT + str(r.json()))
    state["artifacts"] = text  # mutação + string não parseada
    return state
```
