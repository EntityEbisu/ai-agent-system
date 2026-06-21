"""Unit tests for application exception types."""
import pytest

from app.exceptions import (
    AppError,
    LLMConfigError,
    LLMTimeoutError,
    LLMRetryableError,
    RetrieverError,
    WorkflowError,
)


class TestAppError:
    def test_base_error_message_fallback(self):
        """When no log_message is passed, user_message is used as log_message."""
        err = AppError("user visible")
        assert err.user_message == "user visible"
        assert err.log_message == "user visible"
        assert str(err) == "user visible"

    def test_base_error_with_log_message(self):
        """log_message can be explicitly set."""
        err = AppError("user visible", log_message="internal detail")
        assert err.user_message == "user visible"
        assert err.log_message == "internal detail"

    def test_llm_config_error(self):
        err = LLMConfigError("missing OPENROUTER_API_KEY")
        assert "API key" in err.user_message
        assert "missing" in err.log_message

    def test_llm_timeout_error(self):
        err = LLMTimeoutError(timeout_s=30)
        assert "too long" in err.user_message.lower()
        assert "30s" in err.log_message

    def test_llm_retryable_error(self):
        err = LLMRetryableError(status=429, detail="Rate limit hit")
        assert "unavailable" in err.user_message.lower()
        assert "429" in err.log_message

    def test_retriever_error(self):
        err = RetrieverError("Chroma unavailable")
        assert "unavailable" in err.user_message.lower()

    def test_workflow_error(self):
        err = WorkflowError("Graph cycle detected")
        assert "try again" in err.user_message.lower()
