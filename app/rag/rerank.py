"""Re-ranker interface — configurable document reranking for RAG.

Usage::

    from app.rag.rerank import rerank

    docs = rerank(query, retrieved_docs, top_k=5)

When no reranker provider is configured (the default for v1), this module
acts as a no-op pass-through that returns the first *top_k* documents.
"""

from typing import Any

from langchain_core.documents import Document

from config import APIConfig

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def rerank(
    query: str,
    docs: list[Document],
    top_k: int = 5,
) -> list[Document]:
    """Re-rank *docs* by relevance to *query*.

    When ``APIConfig.RERANKER_PROVIDER`` is empty (v1 default), this is a
    no-op that returns ``docs[:top_k]``.

    Future providers (v2):
    - ``"bge-reranker-base"`` — local ``sentence_transformers.CrossEncoder``
    - ``"cohere"`` — Cohere Rerank API (paid)

    Parameters
    ----------
    query:
        The original user query.
    docs:
        Retrieved documents to re-rank.
    top_k:
        Number of documents to keep after re-ranking.

    Returns
    -------
    Re-ranked documents (top-k most relevant).
    """
    provider = (APIConfig.RERANKER_PROVIDER or "").strip().lower()

    if not provider:
        # v1: no-op pass-through
        return docs[:top_k]

    if provider == "bge-reranker-base":
        raise NotImplementedError(
            "bge-reranker-base reranker is a v2 feature. "
            "Install sentence_transformers and configure RERANKER_PROVIDER."
        )

    if provider == "cohere":
        raise NotImplementedError(
            "Cohere Rerank is a paid API — deferred to v2. "
            "See DECISIONS.md for rationale."
        )

    # Unknown provider — warn but pass through
    return docs[:top_k]
