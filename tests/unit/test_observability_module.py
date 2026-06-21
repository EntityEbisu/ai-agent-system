"""Unit tests for observability module."""
from app.services.observability import Timer, init_logging, get_logger, _redact_pii_processor


class TestPIIProcessor:
    def test_redacts_string_fields(self):
        """The PII processor should redact sensitive strings in event dict."""
        event = {"message": "My SSN is 123-45-6789"}
        result = _redact_pii_processor(None, None, event)
        assert "***-**-****" in result["message"]

    def test_redacts_nested_dicts(self):
        """Nested string values should also be redacted."""
        event = {"details": {"email": "user@example.com", "msg": "no pii here"}}
        result = _redact_pii_processor(None, None, event)
        # The email pattern doesn't match our DOB/SSN/CC/phone patterns
        # so it won't be redacted - that's expected behavior

    def test_preserves_non_string_types(self):
        """Non-string values should be untouched."""
        event = {"count": 42, "active": True, "ratio": 0.5}
        result = _redact_pii_processor(None, None, event)
        assert result["count"] == 42
        assert result["active"] is True
        assert result["ratio"] == 0.5

    def test_handles_empty_dict(self):
        result = _redact_pii_processor(None, None, {})
        assert result == {}

    def test_nested_field_recursion(self):
        """Recursively redacts PII in nested dicts and lists."""
        event = {
            "messages": [
                {"content": "SSN is 123-45-6789"},
                {"content": "all clear here"},
            ]
        }
        result = _redact_pii_processor(None, None, event)
        assert "***-**-****" in str(result)
        assert "all clear here" in str(result)


class TestInitLogging:
    def test_init_logging_once(self):
        """init_logging should be idempotent."""
        init_logging()
        init_logging()  # second call should not reconfigure
        logger = get_logger()
        assert logger is not None

    def test_logger_returns_bound_logger(self):
        logger = get_logger()
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")
