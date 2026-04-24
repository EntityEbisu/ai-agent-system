"""
Retriever Interface
Loads persisted ChromaDB and exposes it as a LangChain retriever for RAG pipeline
"""

from langchain_community.vectorstores import Chroma
from app.services.llm import get_embeddings
from config import APIConfig


def get_retriever():
    """
    Load persisted ChromaDB and return as a LangChain retriever.
    Uses the same embedding model as the ingest pipeline.
    
    Returns:
        Chroma retriever instance that can be used in RAG chains
    """
    # Get embeddings using the same model as ingest pipeline
    embeddings = get_embeddings()
    
    # Load persisted ChromaDB
    db = Chroma(
        persist_directory=APIConfig.CHROMA_PERSIST_DIR,
        embedding_function=embeddings
    )
    
    # Return as retriever (can be used directly in LangChain chains)
    return db.as_retriever()
