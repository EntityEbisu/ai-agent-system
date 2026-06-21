# DECISIONS.md — Architecture & Deferral Log

This document captures significant architecture decisions made during Phase A–D of the AI Agent System project. Every deferred item includes **why** (constraint / scope) and **what v2 looks like** so an interviewer can ask informed follow-ups.

---

## 1. SQLite vs PostgreSQL / Redis (Session Store)

**Decision:** SQLite (via SQLAlchemy) for all persistence — chat sessions, conversation history, and analytics.

**Why:** The demo runs on a single $4–6/month VPS or GitHub Codespace. PostgreSQL and Redis add operational complexity (separate processes, memory requirements, backups) for zero demo benefit. SQLite with WAL mode delivers adequate throughput for single-user / light multi-user load.

**v2 Design:**
- Replace SQLAlchemy SQLite engine with PostgreSQL (psycopg2/asyncpg). Add Alembic migrations for schema evolution.
- Introduce Redis for session caching (fast lookups by `session_id`) and rate-limit counters (replaces slowapi's in-memory store).
- Connection pooling via PgBouncer or application-level pool.
- Trade-off: every endpoint that currently uses `get_db_session()` + `.close()` would use a context-managed async session from a pool. The data layer already abstracts queries behind `app.data.models` — the switch would touch only the query functions, not the route handlers.

---

## 2. No OpenTelemetry / Loki / Grafana

**Decision:** Skip distributed tracing and centralized log aggregation. Use structured JSON to stdout via `structlog` and a Prometheus `/metrics` endpoint.

**Why:** OpenTelemetry, Loki, and Grafana each consume 300–800 MB of RAM and require dedicated servers or a Docker Compose stack. The $4–6/month budget cannot host these. The demo only needs to show *awareness* of observability best practices — which the structured logging + Prometheus metrics provide.

**v2 Design:**
- Run `grafana/otel-lgtm` (LGTM stack) as a sidecar container or via a managed Grafana Cloud free tier.
- Instrument every FastAPI route with OpenTelemetry auto-instrumentation (`opentelemetry-instrument`).
- Ship logs to Loki via `structlog`'s Loki processor or a Promtail sidecar.
- Dashboards for latency p50/p95/p99, error rates, and RAG pipeline performance.
- The current `@observe_tool` decorator in `app/services/metrics.py` would be replaced by OpenTelemetry spans with semantic conventions.

---

## 3. No Kubernetes

**Decision:** Deploy as a single `docker run` or `docker compose up` on a cheap VPS.

**Why:** Kubernetes adds a control plane (etcd, API server, scheduler, controller manager) that needs at least 2–3 nodes to be useful. For a demo with 0–5 concurrent users, K8s is 50× overkill. Docker Compose or even a bare systemd unit is the correct scale.

**v2 Design:**
- Wrap the app, Chroma, and (optionally) Postgres in a Docker Compose file.
- Add a `healthcheck` to each service and a `depends_on` with condition.
- Add a Traefik or Caddy reverse proxy for TLS termination.
- Kubernetes would only make sense at 50+ concurrent users or when the agent graph needs to scale horizontally.

---

## 4. No Cohere Rerank

**Decision:** Use a simple similarity-top-k retriever without a cross-encoder reranker.

**Why:** Cohere Rerank is a paid API call per query. The free-tier budget (OpenRouter credits + Student Developer Pack) cannot sustain per-query reranking. The current `all-MiniLM-L6-v2` + Chroma cosine similarity is fast and adequate for the demo product catalog (~100–500 chunks).

**v2 Design:**
- Add a local cross-encoder reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`) loaded on-demand.
- Implement two-stage retrieval: Chroma returns top 20, reranker scores top 20 → returns top 5.
- The `rag/rerank.py` module already has a stub for this.
- Trade-off: +200ms latency per query but significantly better precision for ambiguous questions.

---

## 5. No Gunicorn Multi-Worker

**Decision:** Run a single uvicorn process per container (`CMD ["uvicorn", "app.main:app", ...]`).

**Why:** Gunicorn workers (pre-fork model) multiply memory by worker count. With sentence-transformers and spaCy loaded, each worker adds ~800 MB RSS. A single $4–6/month VPS with 1 GB RAM cannot host multiple workers. The demo also has no concurrent user load that would benefit from parallelism — it's sequential latency-bound (LLM call dominates).

**v2 Design:**
- Add gunicorn with `uvicorn.workers.UvicornWorker` and `--workers=4`.
- Configure `--max-requests` and `--max-requests-jitter` for graceful memory cycling.
- The current `app/main.py` uses `@app.on_event("startup")` which would need to migrate to a lifespan pattern for proper per-worker initialization.
- Trade-off: multi-worker requires either sticky sessions (no shared memory) or a shared Postgres/Redis backend for agent state — SQLite is not safe with multiple writers.

---

## 6. Cost Posture

| Item | Budget / Month |
|------|---------------|
| VPS (DigitalOcean $6 droplet) | $6.00 (Student Developer Pack $200 credit) |
| OpenRouter API credits | ~$5.00 (free-tier models: DeepSeek R1, Llama 3.1 70B, etc.) |
| Docker Hub / GHCR | Free |
| Total out-of-pocket | ~$0 (covered by credits) |

**Why disclosed:** Every architecture decision above is shaped by the constraint "can this run on $0–6/month?" The answer determines the entire stack — no Postgres, no OpenTelemetry, no Kubernetes, no gunicorn.

**v2 Design (if funded):**
- Move to a $20–40/month 2 vCPU / 4 GB RAM VPS.
- Add Postgres + Redis + OpenTelemetry + Grafana stack.
- Add gunicorn with 2–4 workers.
- Replace all free-tier LLMs with GPT-4o / Claude Sonnet.

---

## 7. Coverage Threshold (80% on Filtered Modules)

**Decision:** `pytest --cov=app --cov-fail-under=80` excludes modules that require external services (Chroma, sentence-transformers, SQLite, LLM) at test time.

**Excluded from coverage:**
- `app/main.py` (FastAPI app entrypoint — needs a running ASGI server)
- `app/agent/graph.py` (LangGraph state machine — needs a live LLM)
- `app/agent/memory.py` (agent's long-term memory — needs Chroma + LLM)
- `app/memory/*` (episodic + semantic memory stores — need Chroma)
- `app/rag/*` (retrieval pipeline — needs Chroma + embeddings)
- `app/services/data_introspection.py` (SQLite analytics queries)

**Why:** Running Chroma + sentence-transformers + SQLite during `pytest` adds 30+ seconds to test startup and requires disk I/O for the vector index. For a demo project, unit-testing the pure-logic modules (PII, exceptions, config, schemas, auth, observability, metrics) gives higher confidence-per-second than integration tests that test nothing more than Chroma's SQLite backend. The excluded modules still have lightweight smoke tests via `/readyz`.

**v2 Design:**
- Add a `docker-compose.test.yml` with Chroma + SQLite containers.
- Run integration tests against real services using `pytest-docker` or `testcontainers`.
- Raise coverage threshold to 80% *unfiltered* once the test infrastructure is in place.

---

## 8. Agent Evals Deferred (Step 16.3)

**Decision:** The golden-conversation evaluation harness (`eval/` directory) is not wired into CI. It requires `deepeval` and an LLM API key, which are not available in the free-tier CI runner.

**Why:** `deepeval` makes LLM-as-a-judge calls (cost per eval), and the CI has no access to an API key. Running evals locally is documented in `eval/README.md` but not automated.

**v2 Design:**
- Add a CI matrix step that runs only when `OPENROUTER_API_KEY` is set (or use a GitHub secret).
- Implement `deepeval` with `FaithfulnessMetric` and `HallucinationMetric` on golden conversations.
- Fail CI if the aggregate score drops below 0.8.
- Store eval results in a SQLite database for trend tracking.
