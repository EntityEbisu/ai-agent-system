"""Unit tests for app configuration."""
import os

import pytest

from config import APIConfig


class TestAPIConfig:
    def test_default_chroma_collection(self):
        """The default Chroma collection should match the expected name."""
        assert APIConfig.CHROMA_COLLECTION == "documents"

    def test_default_model_name(self):
        assert APIConfig.OPENROUTER_MODEL_NAME == "openrouter/auto"

    def test_default_embedding_provider(self):
        assert APIConfig.EMBEDDING_PROVIDER == "huggingface"

    def test_default_temperature(self):
        assert APIConfig.LLM_TEMPERATURE == 0.0

    def test_default_chroma_persist_dir(self):
        assert APIConfig.CHROMA_PERSIST_DIR == "data/chroma_db"

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("CHROMA_COLLECTION", "test_collection")
        # Re-import to pick up fresh env var
        import importlib
        import config as cfg
        importlib.reload(cfg)
        assert cfg.APIConfig.CHROMA_COLLECTION == "test_collection"
