"""Shared MiniLM embedder (one model for claims and FAQ indexes)."""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

import numpy as np

from recfair.config import huggingface_token_kwargs

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


class Embedder(Protocol):
    """Port for text embeddings used by FAISS indexes."""

    def encode(self, texts: list[str]) -> np.ndarray:
        """Return L2-normalized float32 matrix of shape (n, dim)."""
        ...


class MiniLMEmbedder:
    """Adapter over ``sentence-transformers`` MiniLM."""

    def __init__(self, model_name: str = EMBEDDING_MODEL) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name, **huggingface_token_kwargs())

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode texts to unit-length vectors for inner-product search."""
        vectors = self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32)


@lru_cache(maxsize=1)
def get_embedder() -> MiniLMEmbedder:
    """Process-wide embedder (lazy download of MiniLM weights)."""
    return MiniLMEmbedder()
