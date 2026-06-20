"""
LLM and Embedding Service Factory
Centralizes model initialization for OpenRouter LLM and HuggingFace embeddings.
Both functions cache their results for singleton reuse.
"""

from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

from config import APIConfig


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Return a cached HuggingFaceEmbeddings singleton (~80 MB model).

    The instance is created once and reused for every subsequent call.
    Config changes require a process restart to take effect.
    """
    embedding_config = APIConfig.get_embedding_config()
    return HuggingFaceEmbeddings(
        model_name=embedding_config["model"]
    )


@lru_cache(maxsize=4)
def get_llm(streaming: bool = False) -> ChatOpenAI:
    """
    Return a cached ChatOpenAI instance keyed by (streaming, model, temperature).

    Args:
        streaming: Whether to enable streaming responses.

    Returns:
        ChatOpenAI instance connected to OpenRouter.
    """
    llm_config = APIConfig.get_llm_config()
    if not llm_config["api_key"]:
        raise ValueError("OPENROUTER_API_KEY must be set in .env for LLM usage.")
    return ChatOpenAI(
        model=llm_config["model"],
        temperature=llm_config["temperature"],
        streaming=streaming,
        openai_api_base=llm_config["api_base"],
        openai_api_key=llm_config["api_key"]  # type: ignore[call-arg]
    )
