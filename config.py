"""
Secure API Key & Configuration Management
This file centralizes all API credentials and environment variables.
Load from .env and expose validated config.
"""

import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class APIConfig:
    """Centralized API configuration with validation"""

    # OpenRouter Configuration
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_API_BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL_NAME = os.getenv("OPENROUTER_MODEL_NAME", "openrouter/auto")

    # Embedding Configuration
    EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "huggingface")  # Options: huggingface, sentence-transformers
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # LLM Configuration
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0))

    # Vector Store Configuration
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "data/chroma_db")

    # Re-ranker Configuration (v2-track — disabled by default)
    RERANKER_PROVIDER = os.getenv("RERANKER_PROVIDER", "")  # "" = none, "bge-reranker-base" for future
    ABSTAIN_THRESHOLD = float(os.getenv("ABSTAIN_THRESHOLD", "0.6"))

    # PDF Configuration
    PDF_PATH = os.getenv("PDF_PATH", "data/docs/Company-10k-18pages.pdf")
    DOCS_DIR = os.getenv("DOCS_DIR", "data/docs")

    @classmethod
    def validate_llm(cls):
        """Validate LLM-specific configuration"""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not set in .env file")
        return True

    @classmethod
    def get_llm_config(cls) -> dict:
        """Return LLM configuration dict"""
        return {
            "model": cls.OPENROUTER_MODEL_NAME,
            "api_base": cls.OPENROUTER_API_BASE,
            "api_key": cls.OPENROUTER_API_KEY,
            "temperature": cls.LLM_TEMPERATURE,
        }

    @classmethod
    def get_embedding_config(cls) -> dict:
        """Return embedding configuration dict"""
        return {
            "provider": cls.EMBEDDING_PROVIDER,
            "model": cls.EMBEDDING_MODEL,
        }


# Configuration validation is performed when an LLM is instantiated, not on import.
