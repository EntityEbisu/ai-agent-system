"""
Prometheus metrics — /metrics endpoint in exposition format.

Provides the metric definitions and a helper to attach the /metrics endpoint
to a FastAPI app.  Replaces the old in-memory ``MetricsCollector``.

Usage::

    from app.services.metrics import setup_metrics, http_requests_total, ...

    setup_metrics(app)

    # Later, in a request handler:
    http_requests_total.labels(endpoint="/chat", status="200").inc()
"""

import time
from typing import Any

from fastapi import FastAPI, Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest

# ---------------------------------------------------------------------------
# HTTP metrics
# ---------------------------------------------------------------------------

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests by endpoint and status code",
    ["endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds by endpoint",
    ["endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

# ---------------------------------------------------------------------------
# LLM metrics
# ---------------------------------------------------------------------------

llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM call duration in seconds by model and operation",
    ["model", "operation"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0),
)

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total tokens consumed by model and role",
    ["model", "role"],
)

# ---------------------------------------------------------------------------
# Tool metrics
# ---------------------------------------------------------------------------

tool_invocations_total = Counter(
    "tool_invocations_total",
    "Total tool invocations by tool name and status",
    ["tool", "status"],
)

tool_duration_seconds = Histogram(
    "tool_duration_seconds",
    "Tool execution duration in seconds by tool name",
    ["tool"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0),
)

# ---------------------------------------------------------------------------
# Retrieval metrics
# ---------------------------------------------------------------------------

retrieval_duration_seconds = Histogram(
    "retrieval_duration_seconds",
    "Vector store retrieval duration in seconds",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0),
)

retrieval_chunks_returned = Counter(
    "retrieval_chunks_returned",
    "Number of chunks returned by collection",
    ["collection"],
)

# ---------------------------------------------------------------------------
# Agent metrics
# ---------------------------------------------------------------------------

agent_iterations_per_session = Histogram(
    "agent_iterations_per_session",
    "Number of agent iterations per session",
    buckets=(1, 2, 3, 4, 5, 6, 7, 8),
)

agent_decision_total = Counter(
    "agent_decision_total",
    "Agent decisions by type",
    ["decision_type"],
)

agent_aborted_total = Counter(
    "agent_aborted_total",
    "Agent aborted sessions by reason",
    ["reason"],
)

# ---------------------------------------------------------------------------
# Cost metrics
# ---------------------------------------------------------------------------

openrouter_spend_usd_total = Counter(
    "openrouter_spend_usd_total",
    "Total spend on OpenRouter in USD",
)

# ---------------------------------------------------------------------------
# Setup helper
# ---------------------------------------------------------------------------

_metrics_app: FastAPI | None = None


def setup_metrics(app: FastAPI) -> None:
    """Attach a ``GET /metrics`` endpoint to *app* that returns Prometheus
    exposition format.

    Call once during application setup (e.g. before ``uvicorn.run``).

    Args:
        app: The FastAPI application instance.
    """
    global _metrics_app
    if _metrics_app is not None:
        return  # already attached

    @app.get("/metrics")
    async def metrics() -> Response:
        """Prometheus metrics endpoint — returns text/plain exposition format."""
        data = generate_latest()
        return Response(
            content=data,
            media_type="text/plain; charset=utf-8",
        )

    _metrics_app = app


# ---------------------------------------------------------------------------
# Convenience wrappers for instrumenting common operations
# ---------------------------------------------------------------------------


def observe_tool(tool_name: str, success: bool, duration_ms: float) -> None:
    """Record a tool invocation.

    Args:
        tool_name: Name of the tool.
        success: Whether the tool executed successfully.
        duration_ms: Execution duration in milliseconds.
    """
    tool_invocations_total.labels(
        tool=tool_name,
        status="success" if success else "error",
    ).inc()
    tool_duration_seconds.labels(tool=tool_name).observe(duration_ms / 1000.0)
