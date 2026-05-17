# 00_ARCHITECTURE_MAP.md

## Runtime Flow & Request Lifecycle

The **entry point** of the application is the FastAPI app defined in `app/main.py`.  When the process starts, the `startup_event` function creates the SQLite database and initialises logging/metrics.

### Main HTTP Endpoints
| Path | Method | Purpose |
|------|--------|---------|
| `/health` | GET | Simple health‑check used by Docker/K8s probes. |
| `/metrics` | GET | Exposes Prometheus‑compatible metrics collected by `app.services.observability`. |
| `/chat` | POST | Core conversational endpoint. It:
  1. Retrieves/creates a session state via `app.agent.memory.get_session`.
  2. Logs the request (observability).
  3. Persists the user message.
  4. Routes the message through `app.agent.router.handle_message_stream` (streaming) or the sync version.
  5. Streams back token chunks to the client.
  6. Persists the assistant response and records latency/token metrics.
| `/api/v1/data/sessions` | GET | Returns a summary of recent conversation sessions (data introspection). |

### Component Interaction Graph (Tier‑1 Runtime)
```
FastAPI (app/main.py) → Router (app/agent/router.py)
    ├─ Tool workflow (app/agent/workflow.py) – when intent == "order_status"
    └─ RAG pipeline (app/rag/pipeline.py) – otherwise
        ├─ LLM (app/services/llm.py)
        └─ Retriever (app/rag/retriever.py) → Vector store (in‑memory / SQLite embeddings)
Session state (app/agent/memory.py) stores per‑session dicts used by router & workflow.
Persistence (app/data/models.py) stores messages & sessions in SQLite.
Observability (app/services/observability.py) provides logging, metrics and a `Timer` context manager.
```

### Actual Execution Graph (Evidence)
The call‑graph is captured in `evidence/runtime_callgraph.md` and shows the concrete function chain from the HTTP request to the final response.

---

*This file is generated purely from code analysis; no assumptions are made from README or infra files.*
