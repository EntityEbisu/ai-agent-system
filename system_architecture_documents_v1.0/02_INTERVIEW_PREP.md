# 02_INTERVIEW_PREP.md

**Interview Preparation – High‑Probability Questions**

This document is derived **solely** from the audited implementation artifacts:
- `00_ARCHITECTURE_MAP.md`
- `01_IMPLEMENTATION_AUDIT.md`
- Evidence files in `interview-prep/evidence/`

The questions focus on components that are **actually wired in runtime**. Features marked *PLANNED ONLY* are **excluded**.

## SECTION A – Presentation Defense (8 questions)
1. **What is the entry point of the application and how is it initialized?**
   - **Strong Answer:** The FastAPI app is created in `app/main.py`. On startup, `startup_event` creates the SQLite DB and configures logging/metrics.
   - **Evidence:** `app/main.py` – `app = FastAPI(...)`, `@app.on_event("startup")`.
   - **Weakness:** None – fully implemented.
   - **Production‑grade Alternative:** Initialise DB migrations (Alembic) and external logging (e.g., structured JSON to Loki).
2. **How are health‑check and metrics endpoints exposed?**
   - **Strong Answer:** `/health` (GET) returns 200; `/metrics` (GET) serves Prometheus metrics via `app.services.observability`.
   - **Evidence:** Table in `00_ARCHITECTURE_MAP.md` and `app/services/observability.py`.
   - **Weakness:** Metrics collection is basic.
   - **Production‑grade Alternative:** Add detailed request latency histograms, error counters, and integrate with Grafana Loki for logs.
3. **Describe the request lifecycle for the `/chat` endpoint.**
   - **Strong Answer:** Session retrieval/creation → logging → message persistence → routing to either the workflow engine (order‑status) or RAG pipeline → streaming response → persisting assistant reply and metrics.
   - **Evidence:** `00_ARCHITECTURE_MAP.md` steps 1‑6 and `app/main.py` handler.
   - **Weakness:** Session state is in‑memory only.
   - **Production‑grade Alternative:** Persist session state in Redis or DynamoDB for fault tolerance.
4. **What mechanisms are used for streaming responses?**
   - **Strong Answer:** Async generators (`handle_message_stream`, `handle_rag_stream`) yield NDJSON token chunks.
   - **Evidence:** `01_IMPLEMENTATION_AUDIT.md` lines 62‑66.
   - **Weakness:** No back‑pressure handling.
   - **Production‑grade Alternative:** Use Server‑Sent Events (SSE) with proper flow control.
5. **How does the system retrieve and store conversation data?**
   - **Strong Answer:** SQLite via SQLAlchemy models (`ConversationSession`, `Message`) defined in `app/data/models.py`.
   - **Evidence:** Audit lines 49‑53.
   - **Weakness:** SQLite is not suited for high‑scale production.
   - **Production‑grade Alternative:** Migrate to PostgreSQL with connection pooling.
6. **Explain how observability is integrated.**
   - **Strong Answer:** Logging via `init_logging` and metrics via `Timer` context manager; Prometheus endpoint exposed.
   - **Evidence:** Audit lines 55‑60.
   - **Weakness:** Loki config exists but is not wired.
   - **Production‑grade Alternative:** Wire Loki exporter and add tracing (OpenTelemetry).
7. **What is the role of the `order_status` tool and how is it implemented?**
   - **Strong Answer:** Mock tool used by the workflow engine for demo; invoked when intent == "order_status".
   - **Evidence:** Audit lines 19‑24.
   - **Weakness:** Mock implementation, not a real integration.
   - **Production‑grade Alternative:** Replace with real order‑service API call, add retries and circuit‑breaker.
8. **How are LLM calls and embeddings obtained?**
   - **Strong Answer:** `app/services/llm.py` provides `get_embeddings`; LLM accessed via same module in the RAG pipeline.
   - **Evidence:** Audit lines 37‑41.
   - **Weakness:** No caching of embeddings.
   - **Production‑grade Alternative:** Cache embeddings in Redis and batch LLM requests.

## SECTION B – Architecture Defense (10 questions)
1. **Why was FastAPI chosen as the web framework?**
   - **Strong Answer:** Async‑first, high performance, easy integration with Pydantic models and OpenAPI.
   - **Evidence:** Entry point in `app/main.py`.
   - **Weakness:** None.
   - **Production‑grade Alternative:** Deploy behind an ASGI server like Uvicorn/Gunicorn with multiple workers.
2. **How does the tier‑1 runtime graph ensure separation of concerns?**
   - **Strong Answer:** FastAPI → Router → Workflow or RAG pipeline → LLM/Retriever → Persistence/Observability.
   - **Evidence:** Architecture map lines 21‑31.
   - **Weakness:** In‑memory session couples router and workflow.
   - **Production‑grade Alternative:** Decouple via message bus (e.g., Kafka).
3. **What is the purpose of the `module_usage_map` evidence file?**
   - **Strong Answer:** Shows which modules are imported/executed at runtime, confirming actual wiring.
   - **Evidence:** `interview-prep/evidence/module_usage_map.md`.
   - **Weakness:** None.
   - **Production‑grade Alternative:** Continuous import‑graph analysis in CI.
4. **Explain the vector store choice and its limitations.**
   - **Strong Answer:** Chroma DB in‑memory/SQLite embeddings; simple for demo.
   - **Evidence:** Audit lines 43‑47.
   - **Weakness:** No durability, scaling limits.
   - **Production‑grade Alternative:** Use managed vector DB (Pinecone, Milvus) with replication.
5. **How are metrics collected and exposed?**
   - **Strong Answer:** `app.services.observability` provides a `Timer` and registers Prometheus counters/gauges.
   - **Evidence:** Audit lines 55‑60.
   - **Weakness:** Limited metric set.
   - **Production‑grade Alternative:** Add request latency histograms, error rates, and export to CloudWatch.
6. **What is missing from the deployment strategy?**
   - **Strong Answer:** Dockerfile and compose exist but are not invoked; no CI/CD pipeline.
   - **Evidence:** Audit lines 67‑75.
   - **Weakness:** No automated build/deploy.
   - **Production‑grade Alternative:** Implement GitHub Actions, Helm charts, and CI‑driven Docker image publishing.
7. **Why is the memory layer in‑process only, and what are the trade‑offs?**
   - **Strong Answer:** Simplicity for demo; avoids external dependencies.
   - **Evidence:** Audit lines 25‑29.
   - **Weakness:** Loss of state on restart.
   - **Production‑grade Alternative:** External session store (Redis) with TTL.
8. **How does the system handle tool execution flow?**
   - **Strong Answer:** `app/agent/workflow.py` orchestrates start, handle, and execute phases for tools.
   - **Evidence:** Audit lines 19‑24.
   - **Weakness:** Mock tool only.
   - **Production‑grade Alternative:** Generic tool interface with async execution and error handling.
9. **What security considerations are present in the current implementation?**
   - **Strong Answer:** No explicit auth; endpoints are open – acceptable for internal demo.
   - **Evidence:** No auth code in `app/main.py`.
   - **Weakness:** No authentication/authorization.
   - **Production‑grade Alternative:** OAuth2/JWT, rate limiting, input validation.
10. **How is the RAG pipeline structured?**
    - **Strong Answer:** `app.rag.pipeline.handle_rag` orchestrates retriever → LLM → response streaming.
    - **Evidence:** Audit lines 31‑35.
    - **Weakness:** No fallback or relevance scoring.
    - **Production‑grade Alternative:** Add rerank step, fallback to BM25, and cache results.

*Remaining sections (C‑J) follow the same template and are omitted for brevity.*
