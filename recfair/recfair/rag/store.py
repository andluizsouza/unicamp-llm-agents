"""FAISS inner-product store with a numpy fallback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from recfair.config import data_dir

try:
    import faiss  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - optional native wheel
    faiss = None


def indexes_dir() -> Path:
    """Directory for persisted vector indexes (gitignored)."""
    path = data_dir() / "indexes"
    path.mkdir(parents=True, exist_ok=True)
    return path


class VectorStore:
    """Cosine search via L2-normalized inner product."""

    def __init__(self, dim: int, metadata: list[dict[str, Any]] | None = None) -> None:
        self.dim = dim
        self.metadata: list[dict[str, Any]] = metadata or []
        self._vectors = np.zeros((0, dim), dtype=np.float32)
        self._index = faiss.IndexFlatIP(dim) if faiss is not None else None

    def add(self, vectors: np.ndarray, metadata: list[dict[str, Any]]) -> None:
        """Append vectors and aligned metadata rows."""
        if vectors.dtype != np.float32:
            vectors = vectors.astype(np.float32)
        if self._index is not None:
            self._index.add(vectors)
        else:
            self._vectors = np.vstack([self._vectors, vectors]) if len(self._vectors) else vectors
        self.metadata.extend(metadata)

    def search(self, query: np.ndarray, k: int = 3) -> list[dict[str, Any]]:
        """Return top-k metadata rows with a ``score`` field."""
        if query.ndim == 1:
            query = query.reshape(1, -1)
        if query.dtype != np.float32:
            query = query.astype(np.float32)
        k = max(1, min(k, len(self.metadata) or 1))
        if self._index is not None and self._index.ntotal > 0:
            scores, ids = self._index.search(query, k)
            hits: list[dict[str, Any]] = []
            for score, idx in zip(scores[0], ids[0], strict=True):
                if idx < 0:
                    continue
                row = dict(self.metadata[int(idx)])
                row["score"] = float(score)
                hits.append(row)
            return hits
        if len(self._vectors) == 0:
            return []
        sims = self._vectors @ query[0]
        order = np.argsort(-sims)[:k]
        hits = []
        for idx in order:
            row = dict(self.metadata[int(idx)])
            row["score"] = float(sims[int(idx)])
            hits.append(row)
        return hits

    def save(self, stem: str) -> Path:
        """Persist index + metadata under ``data/indexes/{stem}.*``."""
        target = indexes_dir() / stem
        meta_path = target.with_suffix(".json")
        meta_path.write_text(
            json.dumps({"dim": self.dim, "metadata": self.metadata}, ensure_ascii=False),
            encoding="utf-8",
        )
        if self._index is not None:
            faiss.write_index(self._index, str(target.with_suffix(".faiss")))
        else:
            np.save(target.with_suffix(".npy"), self._vectors)
        return meta_path

    @classmethod
    def load(cls, stem: str) -> VectorStore:
        """Load a store previously written by ``save``."""
        target = indexes_dir() / stem
        payload = json.loads(target.with_suffix(".json").read_text(encoding="utf-8"))
        store = cls(dim=int(payload["dim"]), metadata=list(payload["metadata"]))
        faiss_path = target.with_suffix(".faiss")
        npy_path = target.with_suffix(".npy")
        if faiss is not None and faiss_path.is_file():
            store._index = faiss.read_index(str(faiss_path))
        elif npy_path.is_file():
            store._vectors = np.load(npy_path)
            store._index = None
        else:
            raise FileNotFoundError(f"Vector index not found for stem={stem}")
        return store
