# 01_IMPLEMENTATION_AUDIT.md

This audit evaluates each requested component against **Tier 1 runtime evidence** (actual executed code paths).  Only features that are imported and exercised during a request are considered *wired in runtime*.

---

## API entrypoint
* **Implementation status:** IMPLEMENTED
* **Runtime usage:** `app/main.py` defines the FastAPI app and registers `/health`, `/metrics`, `/chat`, and `/api/v1/data/sessions`.
* **Missing integrations:** None – all endpoints are reachable.
* **Proof files / functions:** `app/main.py` – `app = FastAPI(...)`, `@app.get("/health")`, `@app.post("/chat")`.

## Agent routing
* **Implementation status:** IMPLEMENTED
* **Runtime usage:** `app/agent/router.py` routes messages based on intent classification.
* **Missing integrations:** None.
* **Proof:** `handle_message`, `handle_message_stream` functions.

## Workflow engine (order‑status tool)
* **Implementation status:** IMPLEMENTED
* **Runtime usage:** Invoked when intent == "order_status"; uses `app/agent/workflow.py`.
* **Missing integrations:** The tool is a mock (`app/tools/order_status.py`) – acceptable for interview demo.
* **Proof:** `start_tool_flow`, `handle_tool_flow`, `execute_tool`.

## Memory
* **Implementation status:** IMPLEMENTED
* **Runtime usage:** In‑memory session store in `app/agent/memory.py` accessed by `/chat`.
* **Missing integrations:** No persistence beyond process lifetime (acceptable for demo).
* **Proof:** `get_session`, `update_session`.

## RAG
* **Implementation status:** IMPLEMENTED
* **Runtime usage:** `app/rag/pipeline.py` handles both sync (`handle_rag`) and streaming (`handle_rag_stream`).
* **Missing integrations:** None – uses retriever and LLM.
* **Proof:** `handle_rag`, `handle_rag_stream`.

## Embeddings
* **Implementation status:** IMPLEMENTED
* **Runtime usage:** `app/services/llm.py` provides `get_embeddings` used by the retriever.
* **Missing integrations:** None.
* **Proof:** `get_embeddings` function.

## Vector store
* **Implementation status:** IMPLEMENTED
* **Runtime usage:** Chroma DB loaded in `app/rag/retriever.py`.
* **Missing integrations:** Persistence directory must exist; not validated at runtime but code loads it.
* **Proof:** `get_retriever` returns `db.as_retriever()`.

## Persistence
* **Implementation status:** IMPLEMENTED
* **Runtime usage:** SQLite DB via SQLAlchemy in `app/data/models.py`; messages persisted in `/chat`.
* **Missing integrations:** None.
* **Proof:** `init_db`, `ConversationSession`, `Message` models; `persist_message` in `app/main.py`.

## Observability
* **Implementation status:** IMPLEMENTED
* **Runtime usage:** Logging and Prometheus metrics via `app/services/observability.py`.
* **Missing integrations:** Loki config exists but is **not wired** – classified as PLANNED ONLY in the feature matrix.
* **Proof:** `init_logging`, `Timer`, `metrics` usage in `app/main.py` and router.

## Streaming
* **Implementation status:** IMPLEMENTED
* **Runtime usage:** Async generator in `handle_message_stream` and `handle_rag_stream` streams NDJSON chunks.
* **Missing integrations:** None.
* **Proof:** `async def handle_message_stream` and `async for chunk in chain.astream`.

## Deployment
* **Implementation status:** PLANNED ONLY
* **Runtime usage:** Dockerfile and `docker-compose.yml` are present but not invoked by the Python runtime.
* **Proof:** No code path triggers container orchestration.

## CI/CD
* **Implementation status:** PLANNED ONLY
* **Runtime usage:** README badge references GitHub Actions, but no workflow files are present.
* **Proof:** Absence of `.github/workflows/` directory.

---

All evidence files referenced above are located in `interview-prep/evidence/`.
