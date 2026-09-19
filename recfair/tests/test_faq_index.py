"""Tests for FAQ KB loading from ``data/kb/faq.pdf`` (LangChain pipeline)."""

from __future__ import annotations

from pathlib import Path

from recfair.rag.faq_index import (
    FAQ_PDF_CHUNK_OVERLAP,
    FAQ_PDF_CHUNK_SIZE,
    FAQ_PDF_NAME,
    REVENDA_CHUNK_OVERLAP,
    REVENDA_CHUNK_SIZE,
    faq_chunks,
    faq_documents,
)


def test_faq_pdf_uses_notebook_chunk_params() -> None:
    pdf_docs = [doc for doc in faq_documents() if doc.metadata.get("tipo_fonte") == "pdf"]
    assert pdf_docs, "expected PDF chunks from faq.pdf"
    assert all(len(doc.page_content) <= FAQ_PDF_CHUNK_SIZE for doc in pdf_docs)
    assert FAQ_PDF_CHUNK_SIZE == 1024
    assert FAQ_PDF_CHUNK_OVERLAP == 120


def test_revenda_uses_notebook_chunk_params() -> None:
    revenda_docs = [
        doc for doc in faq_documents() if Path(doc.metadata.get("source", "")).name == "revenda.md"
    ]
    assert revenda_docs, "expected revenda chunks"
    assert all(len(doc.page_content) <= REVENDA_CHUNK_SIZE for doc in revenda_docs)
    assert REVENDA_CHUNK_SIZE == 512
    assert REVENDA_CHUNK_OVERLAP == 60


def test_faq_chunks_load_pdf_and_revenda() -> None:
    chunks = faq_chunks()
    assert chunks, "expected FAQ KB chunks from faq.pdf and revenda.md"
    sources = {row["source"] for row in chunks}
    assert FAQ_PDF_NAME in sources
    assert "revenda.md" in sources

    payment = next(
        row for row in chunks if row["source"] == FAQ_PDF_NAME and "Visa" in row["excerpt"]
    )
    assert "MasterCard" in payment["excerpt"]
    assert "Elo" in payment["excerpt"]
    assert "Pergunta" in payment["excerpt"]

    revenda_hits = [row for row in chunks if row["source"] == "revenda.md"]
    assert any("flexibilidade" in row["excerpt"].lower() for row in revenda_hits)
