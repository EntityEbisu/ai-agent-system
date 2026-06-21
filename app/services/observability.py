"""
Observability and logging infrastructure (Level 300).

Provides structured logging, metrics tracking, and token usage monitoring.
"""

import json
import logging
import time
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Any

import pythonjsonlogger.jsonlogger

# Context variables for request tracking
request_id: ContextVar[str] = ContextVar('request_id', default='unknown')
session_id: ContextVar[str] = ContextVar('session_id', default='unknown')


class StructuredLogger:
    """Provides structured JSON logging and basic metrics."""

    def __init__(self, name: str, log_file: str | None = None, log_level: str = "INFO"):
        """
        Initialize structured logger.

        Args:
            name: Logger name
            log_file: Path to log file (if None, logs to console only)
            log_level: Logging level (INFO, DEBUG, WARNING, ERROR)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level))
        self.logger.propagate = False

        # Avoid duplicate handlers if logger is initialized multiple times
        if self.logger.handlers:
            return

        # Console handler with JSON formatting
        console_handler = logging.StreamHandler()
        console_formatter = pythonjsonlogger.jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(console_formatter)
            self.logger.addHandler(file_handler)

    def log_request(self, endpoint: str, method: str, session_id: str, message_preview: str):
        """Log incoming request."""
        self.logger.info(
            json.dumps({
                "event": "request_received",
                "endpoint": endpoint,
                "method": method,
                "session_id": session_id,
                "message_preview": message_preview[:50],  # First 50 chars
                "timestamp": datetime.utcnow().isoformat(),
            })
        )

    def log_response(self, endpoint: str, status: str, latency_ms: float, tokens_used: int | None = None,
                    prompt_tokens: int | None = None, completion_tokens: int | None = None):
        """Log response with metrics."""
        event_data = {
            "event": "response_sent",
            "endpoint": endpoint,
            "status": status,
            "latency_ms": latency_ms,
            "tokens_used": tokens_used,
            "timestamp": datetime.utcnow().isoformat(),
        }
        # Add detailed token breakdown if available
        if prompt_tokens is not None:
            event_data["prompt_tokens"] = prompt_tokens
        if completion_tokens is not None:
            event_data["completion_tokens"] = completion_tokens

        self.logger.info(json.dumps(event_data))

    def log_rag_retrieval(self, query: str, chunks_retrieved: int, latency_ms: float):
        """Log RAG retrieval event."""
        self.logger.info(
            json.dumps({
                "event": "rag_retrieval",
                "query_preview": query[:50],
                "chunks_retrieved": chunks_retrieved,
                "latency_ms": latency_ms,
                "timestamp": datetime.utcnow().isoformat(),
            })
        )

    def log_tool_execution(self, tool_name: str, success: bool, latency_ms: float, error: str | None = None):
        """Log tool execution."""
        self.logger.info(
            json.dumps({
                "event": "tool_execution",
                "tool_name": tool_name,
                "success": success,
                "latency_ms": latency_ms,
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
            })
        )

    def log_error(self, error_type: str, message: str, context: dict[str, Any] | None = None):
        """Log error event."""
        self.logger.error(
            json.dumps({
                "event": "error",
                "error_type": error_type,
                "message": message,
                "context": context or {},
                "timestamp": datetime.utcnow().isoformat(),
            })
        )


class MetricsCollector:
    """Simple in-memory metrics collector (Level 300 - E2)."""

    def __init__(self):
        self.metrics: dict[str, Any] = {}

    def record_latency(self, endpoint: str, latency_ms: float):
        """Record endpoint latency."""
        key = f"latency_{endpoint}"
        if key not in self.metrics:
            self.metrics[key] = []
        self.metrics[key].append(latency_ms)

    def record_tokens(self, tokens_used: int, cost_usd: float):
        """Record token usage and cost."""
        if "tokens_used" not in self.metrics:
            self.metrics["tokens_used"] = []
        if "cost_usd" not in self.metrics:
            self.metrics["cost_usd"] = []
        self.metrics["tokens_used"].append(tokens_used)
        self.metrics["cost_usd"].append(cost_usd)

    def record_tool_success(self, tool_name: str, success: bool):
        """Record tool execution result."""
        key = f"tool_success_{tool_name}"
        if key not in self.metrics:
            self.metrics[key] = {"success": 0, "failed": 0}
        if success:
            self.metrics[key]["success"] += 1
        else:
            self.metrics[key]["failed"] += 1

    def get_summary(self) -> dict[str, Any]:
        """Get metrics summary."""
        summary = {}
        for key, values in self.metrics.items():
            if isinstance(values, list):
                summary[key] = {
                    "count": len(values),
                    "avg": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                }
            elif isinstance(values, dict):
                summary[key] = values
        return summary


# Global instances
logger: StructuredLogger | None = None
metrics: MetricsCollector = MetricsCollector()


def init_logging(log_file: str | None = None, log_level: str = "INFO"):
    """Initialize global logger."""
    global logger
    logger = StructuredLogger("ai-agent-system", log_file=log_file, log_level=log_level)


def get_logger() -> StructuredLogger:
    """Get global logger instance."""
    global logger
    if logger is None:
        init_logging()
    # logger is guaranteed non-None after init_logging
    assert logger is not None
    return logger


class Timer:
    """Context manager for timing operations."""

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
