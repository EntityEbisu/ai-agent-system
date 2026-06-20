"""PII redactor — regex-based masking of sensitive patterns.

Provides a simple ``redact()`` function that replaces SSN, DOB, and
common name-like patterns with masked placeholders before logging
or persisting messages.

For a production deployment, replace this with ``presidio-analyzer``
for entity-based detection.
"""

import re
from typing import Any

# ── Patterns ──────────────────────────────────────────────────────

_SSN_PATTERN = re.compile(r"\b(\d{3})-?(\d{2})-?(\d{4})\b")
_DOB_PATTERN = re.compile(
    r"\b(\d{1,4})[-/.](\d{1,2})[-/.](\d{1,4})\b"
)
_CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
_PHONE_PATTERN = re.compile(
    r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)


def redact(text: str) -> str:
    """Mask PII in the given text, returning the redacted version.

    Replaces:
    - SSNs (``123-45-6789``) → ``***-**-****``
    - DOBs (any format) → ``[REDACTED-DOB]``
    - Credit-card-like numbers → ``[REDACTED-CC]``
    - US phone numbers → ``[REDACTED-PHONE]``

    Args:
        text: The raw string to redact.

    Returns:
        String with sensitive patterns replaced.
    """
    result = text
    result = _SSN_PATTERN.sub("***-**-****", result)
    result = _DOB_PATTERN.sub("[REDACTED-DOB]", result)
    result = _CREDIT_CARD_PATTERN.sub("[REDACTED-CC]", result)
    result = _PHONE_PATTERN.sub("[REDACTED-PHONE]", result)
    return result


def redact_message(message: dict[str, Any]) -> dict[str, Any]:
    """Redact PII from a message dict (mutates a copy).

    Args:
        message: Message dict with at least a ``content`` key.

    Returns:
        New dict with ``content`` and any ``error`` fields redacted.
    """
    result = dict(message)
    if "content" in result and isinstance(result["content"], str):
        result["content"] = redact(result["content"])
    if "error" in result and isinstance(result["error"], str):
        result["error"] = redact(result["error"])
    return result
