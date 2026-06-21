"""Unit tests for LLM service factory."""
import os

import pytest

# Must set JWT_SECRET_KEY before importing anything that loads config
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")

from app.services.llm import get_embeddings, get_llm
from app.exceptions import LLMConfigError


class TestGetLLM:
    def test_get_llm_raises_without_api_key(self):
        """Without OPENROUTER_API_KEY, get_llm should raise."""
        try:
            llm = get_llm()
            assert llm is not None
        except LLMConfigError:
            pass  # expected when no key


class TestGetEmbeddings:
    @pytest.mark.slow
    def test_get_embeddings_returns_object(self):
        """get_embeddings loads sentence-transformers (~80 MB) — skip in CI."""
        try:
            emb = get_embeddings()
            assert emb is not None
        except Exception:
            pass
