"""Claim matching: substring (E2 default) with optional per-SKU semantic fallback."""

from __future__ import annotations

from recfair.data.claims import claims_records
from recfair.rag.embedder import get_embedder
from recfair.rag.store import VectorStore, indexes_dir

CLAIMS_INDEX_STEM = "claims"
CLAIMS_MIN_SCORE = 0.38

_STORE: VectorStore | None = None


def _claim_chunks() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for record in claims_records():
        rows.append(
            {
                "sku": record["cod_sku"],
                "claim_type": record["claim_type"],
                "excerpt": record["claim_text"],
            }
        )
    return rows


def build_claims_index() -> VectorStore:
    """Embed each SKU × claim_type chunk and persist FAISS."""
    chunks = _claim_chunks()
    embedder = get_embedder()
    vectors = embedder.encode([row["excerpt"] for row in chunks])
    store = VectorStore(dim=vectors.shape[1])
    store.add(vectors, chunks)
    store.save(CLAIMS_INDEX_STEM)
    return store


def _load_store() -> VectorStore:
    global _STORE
    if _STORE is not None:
        return _STORE
    meta = indexes_dir() / f"{CLAIMS_INDEX_STEM}.json"
    if not meta.is_file():
        raise FileNotFoundError(
            f"Missing claims index {meta}. Run `make data` to build FAISS indexes."
        )
    _STORE = VectorStore.load(CLAIMS_INDEX_STEM)
    return _STORE


def _substring_match(sku: str, terms: list[str]) -> str | None:
    from recfair.tools.scoring.engine import _claim_match

    return _claim_match(sku, terms)


def _semantic_match_sku(sku: str, terms: list[str]) -> str | None:
    """Return the first term that semantically matches a claim chunk for ``sku``."""
    if not terms:
        return None
    embedder = get_embedder()
    store = _load_store()
    k = min(32, max(8, len(store.metadata)))
    for term in terms:
        vector = embedder.encode([term])[0]
        for hit in store.search(vector, k=k):
            if hit.get("sku") != sku:
                continue
            if float(hit.get("score") or 0) >= CLAIMS_MIN_SCORE:
                return term
    return None


def pool_has_substring_match(pool: list[str], terms: list[str]) -> bool:
    """True when any SKU in ``pool`` matches ``terms`` via substring."""
    if not terms:
        return False
    return any(_substring_match(sku, terms) is not None for sku in pool)


def match_substring_or_semantic(sku: str, terms: list[str]) -> str | None:
    """Substring for ``sku``, then semantic fallback when substring misses."""
    hit = _substring_match(sku, terms)
    if hit:
        return hit
    return _semantic_match_sku(sku, terms)


def match_claims_semantic(sku: str, terms: list[str]) -> str | None:
    """Semantic-only matcher (tests and legacy callers)."""
    return _semantic_match_sku(sku, terms)
