"""
Observability — structured logging with structlog, PII redaction, and request context.

Replaces the custom ``StructuredLogger`` with ``structlog`` configured for JSON
output to stdout.  Every log line automatically carries ``request_id``,
``session_id``, and ``user_id`` context vars.  PII is redacted from all string
fields before serialization.

Usage::

    from app.services.observability import get_logger

    logger = get_logger()
    logger.info("request_received", endpoint="/chat", method="POST")
    logger.error("db_write_error", error=str(e), session_id="sess_1")
"""

import logging
import os
import time
from contextvars import ContextVar
from typing import Any

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars, merge_contextvars

from app.pii.redactor import redact

# ---------------------------------------------------------------------------
# Context variables — automatically attached to every log line
# ---------------------------------------------------------------------------

request_id: ContextVar[str] = ContextVar("request_id", default="unknown")
session_id: ContextVar[str] = ContextVar("session_id", default="unknown")
user_id: ContextVar[str] = ContextVar("user_id", default="unknown")

# ---------------------------------------------------------------------------
# PII redaction processor
# ---------------------------------------------------------------------------


def _redact_pii_processor(
    _logger: structlog.stdlib.BoundLogger,
    _method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Run the PII regex redactor over every string field in the event dict.

    This catches PII in log messages, error descriptions, and any other
    string-typed field before serialization.
    """
    for key, value in event_dict.items():
        if isinstance(value, str):
            event_dict[key] = redact(value)
        elif isinstance(value, dict):
            event_dict[key] = _redact_nested(value)
        elif isinstance(value, list):
            event_dict[key] = _redact_list(value)
    return event_dict


def _redact_nested(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively redact strings inside a nested dict."""
    result: dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, str):
            result[k] = redact(v)
        elif isinstance(v, dict):
            result[k] = _redact_nested(v)
        elif isinstance(v, list):
            result[k] = _redact_list(v)
        else:
            result[k] = v
    return result


def _redact_list(items: list[Any]) -> list[Any]:
    """Recursively redact strings inside a list."""
    result: list[Any] = []
    for item in items:
        if isinstance(item, str):
            result.append(redact(item))
        elif isinstance(item, dict):
            result.append(_redact_nested(item))
        elif isinstance(item, list):
            result.append(_redact_list(item))
        else:
            result.append(item)
    return result


# ---------------------------------------------------------------------------
# structlog configuration
# ---------------------------------------------------------------------------

_configured = False


def init_logging(log_file: str | None = None, log_level: str = "INFO") -> None:
    """Configure structlog once at startup.

    Args:
        log_file: Ignored — structlog always writes JSON to stdout.
            (The ``log_file`` parameter is kept for backward compatibility.)
        log_level: Minimum log level (e.g. ``INFO``, ``DEBUG``).
    """
    global _configured
    if _configured:
        return
    _configured = True

    level = getattr(logging, log_level.upper(), logging.INFO)

    structlog.configure(
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            merge_contextvars,
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact_pii_processor,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
    )

    # Set the root logger to the requested level
    logging.getLogger().setLevel(level)
    # Silence noisy third-party loggers
    for name in ("httpx", "httpcore", "urllib3", "chromadb", "sqlalchemy"):
        logging.getLogger(name).setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Logger accessor
# ---------------------------------------------------------------------------

_logger: structlog.stdlib.BoundLogger | None = None


def get_logger() -> structlog.stdlib.BoundLogger:
    """Return the global structlog logger (initialized on first call)."""
    global _logger
    if _logger is None:
        init_logging()
        _logger = structlog.get_logger("ai-agent-system")
    return _logger


def get_logger_instance() -> structlog.stdlib.BoundLogger:
    """Alias for ``get_logger()`` (for backward compatibility)."""
    return get_logger()


# ---------------------------------------------------------------------------
# Request context helper
# ---------------------------------------------------------------------------


def bind_request_context(
    *,
    request_id: str = "unknown",
    session_id: str = "unknown",
    user_id: str = "unknown",
) -> None:
    """Bind context vars for the current request so every log line picks them up.

    Call this at the start of each request (e.g. in a FastAPI middleware).

    Example::

        bind_request_context(
            request_id="req_abc123",
            session_id="sess_456",
            user_id="u1",
        )
    """
    bind_contextvars(
        request_id=request_id,
        session_id=session_id,
        user_id=user_id,
    )


# ---------------------------------------------------------------------------
# Timer — context manager for measuring elapsed time
# ---------------------------------------------------------------------------


class Timer:
    """Context manager that records elapsed wall-clock time in milliseconds.

    Usage::

        with Timer(\"/chat\") as timer:
            ...  # do work

        print(timer.elapsed_ms)  # float
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.start_time: float | None = None
        self.elapsed_ms: float | None = None

    def __enter__(self) -> "Timer":
        self.start_time = time.time()
        return self

    def __exit__(self, *args: object) -> None:
        assert self.start_time is not None
        self.elapsed_ms = (time.time() - self.start_time) * 1000
