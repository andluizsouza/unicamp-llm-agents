"""CLI: rebuild FAQ and claims FAISS indexes (``make data``)."""

from __future__ import annotations

from recfair.config import export_hf_token
from recfair.rag.embedder import EMBEDDING_MODEL
from recfair.rag.faq_index import build_faq_index
from recfair.tools.claims_semantic import build_claims_index


def main() -> None:
    """Build both vector indexes with the shared MiniLM model."""
    if not export_hf_token():
        raise SystemExit(
            "HF_TOKEN is required to download MiniLM weights from Hugging Face. "
            "Copy .env.example to .env and set HF_TOKEN "
            "(https://huggingface.co/settings/tokens)."
        )
    claims = build_claims_index()
    faq = build_faq_index()
    print(
        f"claims vectors={len(claims.metadata)} dim={claims.dim}; "
        f"faq vectors={faq.index.ntotal} model={EMBEDDING_MODEL.split('/')[-1]}"
    )


if __name__ == "__main__":
    main()
