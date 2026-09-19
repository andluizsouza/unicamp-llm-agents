"""Semantic claim matching (multiagent only; E2 gold keeps substring)."""

from __future__ import annotations

from recfair.data.claims import claims_records
from recfair.rag.embedder import get_embedder
from recfair.rag.store import VectorStore, indexes_dir

CLAIMS_INDEX_STEM = "claims"
CLAIMS_MIN_SCORE = 0.38

_STORE: VectorStore | None = None
_TERM_CACHE: dict[tuple[str, ...], dict[str, str]] = {}


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


def _sku_hits_for_terms(terms: list[str]) -> dict[str, str]:
    """Map SKU → highest-scoring claim term above the similarity floor."""
    key = tuple(t.lower() for t in terms)
    cached = _TERM_CACHE.get(key)
    if cached is not None:
        return cached
    embedder = get_embedder()
    store = _load_store()
    mapping: dict[str, str] = {}
    best_score: dict[str, float] = {}
    for term in terms:
        hits = store.search(
            embedder.encode([term])[0],
            k=min(24, max(8, len(store.metadata))),
        )
        for hit in hits:
            score = float(hit.get("score") or 0)
            if score < CLAIMS_MIN_SCORE:
                continue
            sku = hit["sku"]
            if sku not in best_score or score > best_score[sku]:
                best_score[sku] = score
                mapping[sku] = term
    _TERM_CACHE[key] = mapping
    return mapping


def match_claims_semantic(sku: str, terms: list[str]) -> str | None:
    """Return a matched claim term for ``sku``, or ``None``.

    Signature matches ``engine._claim_match`` so the scoring pipeline can
    inject this matcher without changing step order.
    """
    if not terms:
        return None
    return _sku_hits_for_terms(terms).get(sku)
