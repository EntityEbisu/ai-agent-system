# Testing Guide — AI Agent System

This guide covers how to test every component of the system — from automated tests to manual verification procedures.

---

## Table of Contents

1. [Automated Test Suite](#1-automated-test-suite)
2. [Manual Verification Steps](#2-manual-verification-steps)
3. [End-to-End Scenario Walkthrough](#3-end-to-end-scenario-walkthrough)
4. [Performance & Reliability Checks](#4-performance--reliability-checks)
5. [Security Verification](#5-security-verification)
6. [Docker Validation](#6-docker-validation)

---

## 1. Automated Test Suite

The project uses **pytest** with async support. Tests are split into two categories:

### Unit tests (`tests/unit/`)

| Test file | What it covers |
|---|---|
| `test_agent_state.py` | AgentState schema, defaults, reducer logic |
| `test_schemas.py` | Pydantic validation for tool arguments, decision schema |
| `test_tool_registry.py` | Tool registration, argument validation |
| `test_config.py` | Config loading from env, fallbacks |
| `test_pii.py` | PII detection and redaction |
| `test_auth.py` | JWT creation, verification, expiry |
| `test_observability.py` | Structlog configuration, metrics collector |
| `test_metrics.py` | Prometheus metric registration and updates |
| `test_exceptions.py` | AppError hierarchy and error formatting |
| `test_rag_retriever.py` | Chroma retriever initialization and query |
| `test_data_models.py` | SQLAlchemy ORM model CRUD operations |
| `test_llm.py` | LLM client initialization and configuration |

### Integration tests (`tests/integration/`)

| Test file | What it covers |
|---|---|
| `test_api.py` | Full API endpoint tests with httpx AsyncClient |

### Run the full suite

```bash
# From project root
pytest

# With coverage report
pytest --cov=app --cov-report=term-missing

# With verbose output
pytest -v

# Run specific category
pytest tests/unit/
pytest tests/integration/

# Run a specific test file
pytest tests/unit/test_pii.py

# Run a specific test class
pytest tests/integration/test_api.py::TestHealthEndpoint

# Run a specific test
pytest tests/integration/test_api.py::TestHealthEndpoint::test_health_returns_200
```

### Coverage target

The CI pipeline enforces **80%+ code coverage** across the `app/` package:

```bash
pytest --cov=app --cov-fail-under=80
```

### Test configuration

Tests use a dedicated test secret for JWT (set automatically in `conftest.py`):

```python
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
```

No real API keys are needed — LLM calls are mocked via `respx` or not exercised.

---

## 2. Manual Verification Steps

### 2.1 Health & readiness

```bash
# 1. Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. Health check — should return 200
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "1.0.0"}

# 3. Readiness check — should return 200 (Chromadb may warn if not seeded)
curl http://localhost:8000/readyz
# Expected: {"status": "ready", "database": true, "chroma_store": true}
```

### 2.2 Authentication flow

```bash
# 1. Get a JWT token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo-user"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Verify the token works
curl -s http://localhost:8000/api/v1/data/sessions \
  -H "Authorization: Bearer $TOKEN"
# Expected: {"sessions": [...]}

# 3. Verify auth is enforced without token
curl -s http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","message":"hello"}'
# Expected: 401 Unauthorized
```

### 2.3 Chat — Order workflow

```bash
TOKEN="<your-token>"

# Ask about order
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"session_id": "manual-1", "message": "Where is my order?"}'

# Expected: The agent asks for your name.
# Check that the session_id is returned in the response.
```

Continue the multi-turn flow following the responses. After completing the workflow, verify:

- The order status is returned
- The response includes the session_id
- The agent remembers previous turns (same session_id)

### 2.4 Chat — RAG knowledge

If documents have been ingested into Chroma:

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"session_id": "manual-2", "message": "What is your return policy?"}'

# Expected: Response grounded in the ingested documents.
```

### 2.5 Rate limiting

```bash
# Send many rapid requests to trigger rate limit
for i in $(seq 1 70); do
  curl -s -o /dev/null -w "%{http_code} " \
    http://localhost:8000/health
done
# Expected: All 200 (health is exempt from rate limiting)

for i in $(seq 1 70); do
  curl -s -o /dev/null -w "%{http_code} " \
    -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"session_id":"test","message":"hi"}'
done
# Expected: Most 200, eventually some 429
```

### 2.6 Prometheus metrics

```bash
curl http://localhost:8000/metrics
# Expected: Plaintext Prometheus output with http_requests_total,
# http_request_duration_seconds, tool_duration_seconds, etc.
```

### 2.7 Data visibility endpoints

```bash
# List sessions
curl -s http://localhost:8000/api/v1/data/sessions \
  -H "Authorization: Bearer $TOKEN"

# Get session details (PII should be redacted)
curl -s http://localhost:8000/api/v1/data/sessions/manual-1 \
  -H "Authorization: Bearer $TOKEN"

# Analytics snapshot
curl -s http://localhost:8000/api/v1/data/analytics/snapshot \
  -H "Authorization: Bearer $TOKEN"

# Token usage
curl -s "http://localhost:8000/api/v1/data/analytics/tokens?hours=24" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 3. End-to-End Scenario Walkthrough

This is the **demo script** — run through these steps in order to show a complete system walkthrough.

### Scenario A: Order status lookup

```
Step 1: Get a JWT token
Step 2: Start a chat session → "Where is my order?"
Step 3: Provide name → "John Doe"
Step 4: Provide SSN last-4 → "1234"
Step 5: Provide DOB → "1990-01-15"
Step 6: Receive order status → "Your order #12345 has been shipped..."
Step 7: Ask a follow-up → "When will it arrive?"
Step 8: Verify the agent remembers the context
```

### Scenario B: Knowledge base query (if Chroma is seeded)

```
Step 1: Start a new session → "What is your return policy?"
Step 2: Verify the response cites specific documents
Step 3: Check that the response is grounded, not generic
```

### Scenario C: Error handling

```
Step 1: Send empty session_id → observe graceful handling
Step 2: Send invalid JWT → 401 response
Step 3: Send malformed body → 422 validation error
```

---

## 4. Performance & Reliability Checks

### Cold start

```bash
# Start the server, measure time to first request
time curl http://localhost:8000/health
# Expected: < 2 seconds (includes Chroma init and model loading)
# Note: first RAG query may be slower due to embedding model cold start
```

### Concurrent requests

```bash
# Install parallel tool
sudo apt-get install -y parallel

# Send 10 concurrent chat requests
seq 1 10 | parallel -j10 \
  "curl -s -X POST http://localhost:8000/chat \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer $TOKEN' \
    -d '{\"session_id\":\"perf-{}\",\"message\":\"hi\"}'"
# Expected: All return 200, no crashes
```

### Long-running session

```bash
# Run a 20-turn conversation
for turn in $(seq 1 20); do
  curl -s -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"session_id\":\"long-1\",\"message\":\"turn $turn\"}"
  sleep 0.5
done
# Expected: All responses succeed, memory doesn't grow unbounded
```

---

## 5. Security Verification

Check these manually or via the test suite:

| Check | How to verify |
|---|---|
| JWT auth on /chat | `curl /chat` without token → 401 |
| JWT auth on data endpoints | `curl /api/v1/data/sessions` without token → 401 |
| JWT auth NOT on /health | `curl /health` → 200 (no token needed) |
| JWT auth NOT on /metrics | `curl /metrics` → 200 (no token needed) |
| PII redaction in logs | Check `logs/app.log` for user messages — SSN/M among... |
| PII redaction in API | `GET /api/v1/data/sessions/{id}` — messages should have PII masked |
| HSTS security header | `curl -I /chat` → `Strict-Transport-Security: max-age=31536000` |
| Rate limiting | Rapid requests → eventual `429 Too Many Requests` |
| Input validation | Malformed SSN/DOB → validation error, not server crash |
| Path traversal | `GET /api/v1/data/sessions/../etc/passwd` → 404, not file read |

---

## 6. Docker Validation

> ⚠️ **Disk constraint:** Each `docker build` consumes ~5.6 GB (2.3 GB image + 3.3 GB cache). On a 32 GB Codespace, run this only when you have >10 GB free. Always prune after use.

### Build

```bash
# Validate Dockerfile syntax (zero disk cost)
docker build --check .

# Full build (consumes ~5.6 GB — only when needed)
docker build -t ai-agent-system .

# Prune cache to reclaim space
docker system prune -f
```

### Verify image size

```bash
docker images ai-agent-system
# Expected: < 2 GB final image (multi-stage build removes build deps)
```

### Run container

```bash
# Create .env for the container
docker run -d \
  --name ai-agent \
  -p 8000:8000 \
  --env-file .env \
  ai-agent-system

# Verify it's running
curl http://localhost:8000/health
curl http://localhost:8000/readyz

# Clean up
docker stop ai-agent && docker rm ai-agent
docker system prune -f
```

---

## Quick reference — testing checklist

Use this to ensure everything is working before a demo:

- [ ] `pytest` passes (all tests green)
- [ ] `pytest --cov=app --cov-fail-under=80` passes
- [ ] `GET /health` → 200
- [ ] `GET /readyz` → 200 (or `chroma_warn` is expected)
- [ ] `POST /api/v1/auth/token` → returns JWT
- [ ] `POST /chat` with valid token → 200
- [ ] `POST /chat` without token → 401
- [ ] Multi-turn order workflow completes successfully
- [ ] `GET /metrics` returns Prometheus output
- [ ] `docker build --check .` passes (Dockerfile syntax valid)
- [ ] `docker build -t ai-agent-system` builds successfully (if space allows)
- [ ] CI workflow runs on push (check GitHub Actions tab)
