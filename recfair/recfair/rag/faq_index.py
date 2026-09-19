"""FAQ retrieval — LangChain pipeline aligned with hands_on_final_test.ipynb."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from recfair.config import data_dir, huggingface_token_kwargs
from recfair.rag.store import indexes_dir

FAQ_INDEX_STEM = "faq"
FAQ_K = 5
FAQ_PDF_NAME = "faq.pdf"
REVENDA_MD_NAME = "revenda.md"

# PDF FAQ — config C_longo from hands_on_final_test.ipynb (chunk_pdf_longo).
FAQ_PDF_CHUNK_SIZE = 1024
FAQ_PDF_CHUNK_OVERLAP = 120

# Revenda TXT analogue — config B_medio (chunk_txt_medio).
REVENDA_CHUNK_SIZE = 512
REVENDA_CHUNK_OVERLAP = 60

SPLITTER_SEPARATORS = ["\n\n", "\n", " ", ""]
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def kb_dir() -> Path:
    """Directory with versioned FAQ knowledge-base files."""
    return data_dir() / "kb"


def _faq_index_dir() -> Path:
    return indexes_dir() / FAQ_INDEX_STEM


@lru_cache(maxsize=1)
def _embeddings() -> HuggingFaceEmbeddings:
    """Same MiniLM setup as the course notebook (COSINE + normalized vectors)."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu", **huggingface_token_kwargs()},
        encode_kwargs={"normalize_embeddings": True},
    )


def _splitter(*, chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=SPLITTER_SEPARATORS,
        length_function=len,
    )


def _load_pdf_documents(path: Path) -> list[Document]:
    docs = PyPDFLoader(str(path)).load()
    for doc in docs:
        doc.metadata["tipo_fonte"] = "pdf"
        doc.metadata["source"] = str(path)
    return docs


def _load_revenda_documents(path: Path) -> list[Document]:
    text = path.read_text(encoding="utf-8")
    return [
        Document(
            page_content=text,
            metadata={"tipo_fonte": "txt", "source": str(path)},
        )
    ]


def faq_documents() -> list[Document]:
    """Load and chunk FAQ PDF + revenda markdown with notebook-aligned params."""
    docs: list[Document] = []

    faq_pdf = kb_dir() / FAQ_PDF_NAME
    if faq_pdf.is_file():
        pdf_docs = _load_pdf_documents(faq_pdf)
        docs.extend(
            _splitter(
                chunk_size=FAQ_PDF_CHUNK_SIZE,
                chunk_overlap=FAQ_PDF_CHUNK_OVERLAP,
            ).split_documents(pdf_docs)
        )

    revenda_md = kb_dir() / REVENDA_MD_NAME
    if revenda_md.is_file():
        revenda_docs = _load_revenda_documents(revenda_md)
        docs.extend(
            _splitter(
                chunk_size=REVENDA_CHUNK_SIZE,
                chunk_overlap=REVENDA_CHUNK_OVERLAP,
            ).split_documents(revenda_docs)
        )

    return docs


def faq_chunks() -> list[dict[str, str]]:
    """Return chunk rows for tests and debugging."""
    return [
        {
            "source": Path(doc.metadata.get("source", "?")).name,
            "excerpt": doc.page_content,
        }
        for doc in faq_documents()
    ]


def build_faq_index() -> FAISS:
    """Embed FAQ chunks with LangChain FAISS (COSINE) and persist under ``data/indexes/faq/``."""
    documents = faq_documents()
    if not documents:
        raise FileNotFoundError(
            f"No FAQ KB files under {kb_dir()} "
            f"(expected {FAQ_PDF_NAME} and/or {REVENDA_MD_NAME})"
        )

    store = FAISS.from_documents(
        documents=documents,
        embedding=_embeddings(),
        distance_strategy="COSINE",
    )
    target = _faq_index_dir()
    target.mkdir(parents=True, exist_ok=True)
    store.save_local(str(target))
    return store


_FAQ_STORE: FAISS | None = None


def _load_store() -> FAISS:
    global _FAQ_STORE
    if _FAQ_STORE is not None:
        return _FAQ_STORE

    target = _faq_index_dir()
    if not target.is_dir():
        raise FileNotFoundError(
            f"Missing FAQ index directory {target}. Run `make data` to build FAISS indexes."
        )

    _FAQ_STORE = FAISS.load_local(
        str(target),
        _embeddings(),
        allow_dangerous_deserialization=True,
    )
    return _FAQ_STORE


def retrieve_faq(query: str, *, k: int = FAQ_K) -> list[dict[str, Any]]:
    """Return top-k FAQ chunks with LangChain relevance scores (no score threshold)."""
    store = _load_store()
    results = store.similarity_search_with_relevance_scores(query, k=k)
    hits: list[dict[str, Any]] = []
    for doc, score in results:
        hits.append(
            {
                "source": Path(doc.metadata.get("source", "?")).name,
                "excerpt": doc.page_content,
                "score": float(score),
                "tipo_fonte": doc.metadata.get("tipo_fonte"),
            }
        )
    return hits
