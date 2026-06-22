# Usage Guide — AI Agent System

This guide covers every endpoint, workflow, and feature of the e-commerce customer support chatbot.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [API Endpoints Reference](#api-endpoints-reference)
3. [Authentication](#authentication)
4. [Chat Workflow](#chat-workflow)
5. [Data Visibility & Analytics](#data-visibility--analytics)
6. [Streamlit Frontend](#streamlit-frontend)
7. [Common Scenarios](#common-scenarios)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Python 3.11+
- An OpenRouter API key (set in `.env` as `OPENROUTER_API_KEY`)
- ~2 GB free RAM

### Start the system

```bash
# Terminal 1 — API server
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend (optional)
source venv/bin/activate
streamlit run frontend/streamlit_app.py
```

### Verify it's running

```bash
curl http://localhost:8000/health
# → {"status": "healthy", "version": "1.0.0"}
```

---

## API Endpoints Reference

### Public (no auth required)

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check — returns `{"status": "healthy"}` |
| `GET` | `/readyz` | Readiness check — verifies DB + Chroma store |
| `GET` | `/metrics` | Prometheus metrics (text exposition format) |
| `POST` | `/api/v1/auth/token` | Issue a demo JWT token |

### Requires JWT Bearer token

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat` | Send a message to the agent |
| `GET` | `/api/v1/data/sessions` | List recent sessions |
| `GET` | `/api/v1/data/sessions/{id}` | Get session message history |
| `GET` | `/api/v1/data/analytics/snapshot` | System metrics snapshot |
| `GET` | `/api/v1/data/analytics/tokens` | Token usage report |

---

## Authentication

All endpoints except `/health`, `/readyz`, `/metrics`, and `/api/v1/auth/token` require a JWT Bearer token.

### Get a token

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo-user"}'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Use the token

Include it as a Bearer header on authenticated requests:

```bash
TOKEN="eyJhbGciOiJIUzI1NiIs..."

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"session_id": "test-1", "message": "Where is my order?"}'
```

### How JWT is configured

- **Signing key:** Set via `JWT_SECRET_KEY` in `.env`
- **Generation:** `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- **Token expiry:** Configurable (default TBD in `app/auth/jwt_handler.py`)
- **For tests:** `JWT_SECRET_KEY=test-secret-key-for-testing-only`

---

## Chat Workflow

### Conversation flow

The agent follows a structured ReAct loop:

```
User message
  → Intent classification (order vs knowledge vs fallback)
  → If "order status":
      → Collect missing slot (name → SSN last-4 → DOB)
      → Validate each input
      → Execute tool when all slots are filled
      → Return result
  → If "knowledge":
      → Retrieve relevant documents from Chroma
      → Generate answer with citations
      → Return response
  → If "fallback":
      → Answer from LLM knowledge (no retrieval)
```

### Basic chat

```bash
TOKEN="<your-token>"

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"session_id": "demo-1", "message": "Where is my order?"}'
```

Response:

```json
{
  "response": "Please provide your full name to check your order status.",
  "session_id": "demo-1"
}
```

### Multi-turn order workflow

```bash
# Turn 1 — ask about order
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"session_id": "order-1", "message": "Where is my order?"}'
# → "Please provide your full name."

# Turn 2 — provide name
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"session_id": "order-1", "message": "John Doe"}'
# → "Please provide the last 4 digits of your SSN."

# Turn 3 — provide SSN
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"session_id": "order-1", "message": "1234"}'
# → "Please provide your date of birth (YYYY-MM-DD)."

# Turn 4 — provide DOB
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"session_id": "order-1", "message": "1990-01-15"}'
# → "Your order #12345 has been shipped and is expected to arrive in 2 days."
```

### RAG knowledge queries

```bash
# Ask a policy / knowledge question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"session_id": "know-1", "message": "What is your return policy?"}'
# → Response grounded in ingested documents with citations
```

### Session reuse

Use the same `session_id` to continue a conversation. The agent maintains:

- **Episodic memory:** Summaries of previous conversations
- **Semantic memory:** Facts extracted from user interactions
- **Working memory:** Current slot-filling state (for order workflow)

```bash
# Continue previous session
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"session_id": "demo-1", "message": "Actually, when will it arrive?"}'
```

---

## Data Visibility & Analytics

### List recent sessions

```bash
curl http://localhost:8000/api/v1/data/sessions?limit=10 \
  -H "Authorization: Bearer $TOKEN"
```

### View session messages

```bash
curl http://localhost:8000/api/v1/data/sessions/demo-1 \
  -H "Authorization: Bearer $TOKEN"
```

Messages are **PII-redacted** before serving (SSN numbers masked, etc.).

### Analytics snapshot

```bash
curl http://localhost:8000/api/v1/data/analytics/snapshot \
  -H "Authorization: Bearer $TOKEN"
```

### Token usage report

```bash
# Last 24 hours by default
curl "http://localhost:8000/api/v1/data/analytics/tokens?hours=24" \
  -H "Authorization: Bearer $TOKEN"
```

### Prometheus metrics

```bash
curl http://localhost:8000/metrics
# Returns plain-text Prometheus exposition format:
#   http_requests_total{endpoint="/chat",status="200"} 42.0
#   http_request_duration_seconds{endpoint="/chat"} ...
```

---

## Streamlit Frontend

The Streamlit UI provides an interactive chat interface plus data exploration:

```bash
streamlit run frontend/streamlit_app.py
```

Features:

- Chat with the agent through a web UI
- View session history with message timelines
- Explore embedded documents in the Chroma store
- View logs and metrics in-browser
- Authentication: enter your JWT token in the sidebar

---

## Common Scenarios

### Order status check

```
User: Where is my order?
Agent: collects name → SSN last-4 → DOB → validates → returns status
```

### Return / refund inquiry

```
User: I want to return an item
Agent: collects name → SSN last-4 → DOB → validates → returns policy
```

### Product information

```
User: What are your shipping options?
Agent: retrieves relevant documents → answers with citations
```

### Multi-intent / fallback

```
User: Tell me a joke
Agent: falls back to LLM knowledge (no retrieval)
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `401 Unauthorized` on `/chat` | Missing or expired JWT token | Get a new token via `POST /api/v1/auth/token` |
| `429 Too Many Requests` | Rate limit hit | Wait 1 minute (60 req/min authenticated, 10/min unauthenticated) |
| `{"error": "OPENROUTER_API_KEY not set"}` | Missing API key | Add `OPENROUTER_API_KEY` to `.env` |
| Chroma errors in logs | No documents ingested | Run seed script or upload a PDF via the frontend |
| `/readyz` returns `chroma_warn` | Chroma store not seeded | Ingest documents first |
| Docker build fails | Out of disk space | Run `docker system prune -f` to reclaim space |
