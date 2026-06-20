"""
LLM and Embedding Service Factory
Centralizes model initialization for OpenRouter LLM and HuggingFace embeddings
"""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

from config import APIConfig


def get_llm(streaming: bool = False):
    """
    Returns an LLM instance configured for OpenRouter.
    Args:
        streaming: Whether to enable streaming responses
    Returns:
        ChatOpenAI instance connected to OpenRouter
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


def get_embeddings():
    """
    Returns an embeddings instance using HuggingFace.
    Uses a lightweight, local model that doesn't require API keys.
    Returns:
        HuggingFaceEmbeddings instance
    """
    embedding_config = APIConfig.get_embedding_config()
    return HuggingFaceEmbeddings(
        model_name=embedding_config["model"]
    )
