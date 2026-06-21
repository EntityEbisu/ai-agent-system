"""Semantic chunker factory — replaces RecursiveCharacterTextSplitter.

Uses ``langchain_experimental.text_splitter.SemanticChunker`` to split
documents at semantic boundaries (sentence-embedding distance spikes)
rather than at fixed character counts.
"""

from langchain_experimental.text_splitter import SemanticChunker

from app.services.llm import get_embeddings

# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_semantic_chunker: SemanticChunker | None = None


def get_semantic_chunker() -> SemanticChunker:
    """Return a cached :class:`SemanticChunker` instance.

    The chunker uses the same ``get_embeddings()`` singleton as the rest
    of the pipeline so the vector space is consistent.
    """
    global _semantic_chunker
    if _semantic_chunker is None:
        embeddings = get_embeddings()
        _semantic_chunker = SemanticChunker(
            embeddings=embeddings,
            breakpoint_threshold_type="percentile",  # sensible default
        )
    return _semantic_chunker
