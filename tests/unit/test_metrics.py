"""Unit tests for Prometheus metrics module."""
from app.services.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    setup_metrics,
    observe_tool,
    tool_invocations_total,
    tool_duration_seconds,
)


class TestMetrics:
    def test_http_counter(self):
        http_requests_total.labels(endpoint="/test", status="200").inc()
        # No exception = metric registered

    def test_http_duration(self):
        http_request_duration_seconds.labels(endpoint="/test").observe(0.5)

    def test_tool_observe(self):
        observe_tool(tool_name="test_tool", success=True, duration_ms=100)
        # Verify counter incremented
        metric = tool_invocations_total.labels(
            tool="test_tool", status="success"
        )
        assert metric._value.get() >= 1.0
