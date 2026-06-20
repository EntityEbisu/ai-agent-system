"""
Retriever Interface
Loads persisted ChromaDB and exposes it as a LangChain retriever for RAG pipeline.

The retriever (and its backing embedding model) are created once and cached
to avoid reloading ~80 MB of model weights on every request.
"""

import threading

from langchain_community.vectorstores import Chroma

from app.services.llm import get_embeddings
from config import APIConfig

_retriever = None
_retriever_lock = threading.Lock()


def get_retriever():
    """
    Load persisted ChromaDB and return as a LangChain retriever.

    The retriever is cached after construction so that subsequent calls
    reuse the same instance. Thread-safe via double-checked locking.

    Returns:
        Chroma retriever instance that can be used in RAG chains.
    """
    global _retriever
    if _retriever is None:
        with _retriever_lock:
            if _retriever is None:
                embeddings = get_embeddings()
                db = Chroma(
                    persist_directory=APIConfig.CHROMA_PERSIST_DIR,
                    embedding_function=embeddings,
                )
                _retriever = db.as_retriever()
    return _retriever
