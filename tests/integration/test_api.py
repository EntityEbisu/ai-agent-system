"""API integration tests — health, readyz, auth token, metrics.

Uses ``httpx.AsyncClient`` with ``ASGITransport`` to exercise the FastAPI app
without running a full ASGI server.  External HTTP calls (OpenRouter, etc.) are
mocked with ``respx``.
"""
import os

import pytest
from httpx import ASGITransport, AsyncClient

# Set required env vars before importing app
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")


@pytest.fixture(autouse=True)
def _set_env():
    """Ensure JWT_SECRET_KEY is set before each test."""
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")


from app.main import app  # noqa: E402


@pytest.fixture
async def client():
    """Provide an async test client attached to the FastAPI app."""
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    """GET /health — no auth required."""

    async def test_health_returns_200(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert body["version"] == "1.0.0"


class TestReadyzEndpoint:
    """GET /readyz — no auth required."""

    async def test_readyz_returns_200_when_db_writable(self, client: AsyncClient):
        """DB initializes when the data dir is writable."""
        resp = await client.get("/readyz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ready"


class TestMetricsEndpoint:
    """GET /metrics — no auth required, Prometheus exposition format."""

    async def test_metrics_returns_prometheus_format(self, client: AsyncClient):
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/plain; charset=utf-8"
        text = resp.text
        # Should contain at least some Prometheus metric names
        assert "# HELP" in text or "http_requests" in text


class TestAuthTokenEndpoint:
    """POST /api/v1/auth/token — no auth required (demo endpoint)."""

    async def test_issue_token(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/token",
            json={"user_id": "test-user"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"


class TestChatEndpointNoAuth:
    """POST /chat — requires JWT, should reject without one."""

    async def test_chat_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            "/chat",
            json={"session_id": "sess_1", "message": "Hello"},
        )
        assert resp.status_code == 401  # Unauthorized when no token provided


class TestDataEndpointsNoAuth:
    """Endpoints under /api/v1/data/ — require JWT."""

    async def test_sessions_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/data/sessions")
        assert resp.status_code == 401

    async def test_analytics_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/data/analytics/snapshot")
        assert resp.status_code == 401


class TestSecurityHeaders:
    """Security headers should be present on every response."""

    async def test_hsts_header(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.headers.get("strict-transport-security") is not None
        assert "max-age=31536000" in resp.headers["strict-transport-security"]
