"""Unit tests for PII redaction."""
import pytest

from app.pii.redactor import redact, redact_message


class TestRedact:
    def test_redacts_ssn(self):
        assert redact("My SSN is 123-45-6789") == "My SSN is ***-**-****"

    def test_redacts_dob(self):
        assert "12/31/1990" != redact("Born 12/31/1990")
        assert "[REDACTED-DOB]" in redact("Born 12/31/1990")

    def test_redacts_credit_card(self):
        result = redact("Card: 4111111111111111")
        assert "[REDACTED-CC]" in result

    def test_redacts_phone(self):
        result = redact("Call 555-123-4567")
        assert "[REDACTED-PHONE]" in result

    def test_preserves_normal_text(self):
        msg = "Hello, how can I help you?"
        assert redact(msg) == msg

    def test_handles_mixed_content(self):
        result = redact("Contact support at 555-123-4567 or use SSN 123-45-6789")
        assert "[REDACTED-PHONE]" in result
        assert "***-**-****" in result

    def test_handles_empty_string(self):
        assert redact("") == ""

    def test_redact_message_dict(self):
        msg = {"role": "user", "content": "my dob is 01/15/1990"}
        result = redact_message(msg)
        assert "[REDACTED-DOB]" in result["content"]
        assert result["role"] == "user"  # role untouched

    def test_redact_message_error_field(self):
        msg = {"error": "user SSN is 123-45-6789"}
        result = redact_message(msg)
        assert "***-**-****" in result["error"]
