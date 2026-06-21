# Phase D-lite — Tests, CI, Security & Minimal Deploy (Selected Steps)

**Theme:** Make the repo testable, verifiable, and deployable at minimal cost. This is a **scoped-down subset** of the original Phase D (full plan available in the original `ai-agent-system-audit-report.md`). Items deferred to "v2" are documented in a `DECISIONS.md` file so interviewers can ask about them.

**Rationale for scope reduction:** This is a personal demo project, not a production service. Full OpenTelemetry + Prometheus + Loki + Grafana stack would consume more RAM than the app itself on a $6/month DigitalOcean droplet. Postgres + Alembic migration would add complexity with zero visible benefit to a recruiter evaluating the agent rebuild. Kubernetes is absurd overkill for a single-user demo. These deferrals are documented as deliberate trade-offs, not omissions.

**Entry criteria:** Phase B and C complete. The agent runs, has memory, has decent RAG.

**Exit criteria:** Real passing CI workflow (ruff, mypy, pytest, docker build), ≥80% test coverage on core packages, `/readyz` endpoint pinging dependencies, clean Dockerfile, and a `DECISIONS.md` that explains the deferred items and how you'd approach them at scale.

---

## Step 15: Basic observability improvements (no OTel, no Loki)

The current "observability" is a `print()`-style JSON logger and an in-memory metric dict. It is reset on every process restart. The `/metrics` endpoint returns custom JSON, not Prometheus exposition format.

Note: **OpenTelemetry tracing, Loki log aggregation, and Prometheus scraping** are deferred to v2. They would add meaningful insight at scale but require running a collector sidecar + Grafana, which is ~500 MB RAM overhead on a 1 GB droplet. Document the v2 design in `DECISIONS.md`.

### 15.1 Structured logging with `structlog`
- **What:** replace the custom `StructuredLogger` in `app/services/observability.py` with `structlog` configured for JSON output to stdout. Add a context var (`request_id`, `session_id`, `user_id`) that every log line picks up.
- **PII redaction:** add a `structlog` processor that runs the PII regex redactor (from Phase A Step 4) over every string field before serialization.
- **Library:** `structlog`.

### 15.2 Real `/metrics` endpoint in Prometheus exposition format
- **What:** replace the custom JSON `/metrics` endpoint with `prometheus_client` returning text/plain exposition format so Prometheus *could* scrape it. Required metrics:
  - **HTTP:** `http_requests_total{endpoint,status}`, `http_request_duration_seconds{endpoint}` (histogram)
  - **LLM:** `llm_request_duration_seconds{model,operation}`, `llm_tokens_total{model,role}`
  - **Tools:** `tool_invocations_total{tool,status}`, `tool_duration_seconds{tool}` (histogram)
  - **Retrieval:** `retrieval_duration_seconds`, `retrieval_chunks_returned{collection}`
  - **Agent-specific:**
    - `agent_iterations_per_session` (histogram)
    - `agent_decision_total{decision_type}` (counter)
    - `agent_aborted_total{reason}` (counter)
  - **Cost:** `openrouter_spend_usd_total` so a budget alert can fire
- **Note:** Prometheus itself is not deployed on the droplet. The metrics endpoint exists so that (a) a recruiter can `curl /metrics` and see real data, and (b) if you later add Prometheus + Grafana, the endpoint is ready. The existing `observability/prometheus.yml` and `loki-config.yml` files are **stale configs from the previous design** — update them to reflect the current architecture or delete them.
- **Library:** `prometheus_client`.

### 15.3 Deferred items (document in DECISIONS.md)
The following are explicitly deferred to v2:
- **OpenTelemetry tracing** — instrumenting FastAPI + LangGraph + LLM calls with OTLP export to Tempo/Jaeger. Design: each graph node emits a span; the `reasoning` field from the `Decision` structured output becomes a span attribute. Cost: ~$0 (OSS collector) but adds ~300 MB RAM.
- **Loki log aggregation** — wiring `structlog` stdout through an OTel collector into Loki. Already designed; just missing the collector container.
- **SLO dashboards / alerts** — Grafana dashboards for p95 latency, abstain rate, budget. Would exist if Grafana were deployed.
- **Agent-specific metric dashboards** — `agent_decision_total`, `citation_rate`, etc. The metrics are exposed; only the dashboard is missing.

**Pattern:** Instrument early, visualize later · Cost-conscious monitoring.

**Library:** `structlog`, `prometheus_client`.

**Acceptance:**
- `curl /metrics` returns text/plain in Prometheus exposition format
- Log lines are JSON with `request_id`, `session_id`, `user_id` context vars
- No PII appears in log output
- The DECISIONS.md file describes the deferred OTel/Loki/Grafana design in enough detail to answer interview questions

---

## Step 16: Tests, CI/CD, security

Zero tests today. The audit says "no workflow files" — but `.github/workflows/ci.yml` **already exists** with lint, test, and security jobs targeting Python 3.13. It references `scripts/validate_project.py` and `tests/run_all_tests.py` that don't exist yet. Step 16 makes all of this real.

### 16.1 Unit tests with `pytest`
- **What:** write `tests/unit/` for:
  - State transitions in the LangGraph graph (snapshot tests of the state at each node)
  - Tool schemas (Pydantic validation: valid and invalid inputs)
  - Memory tier read/write/evict
  - RAG pipeline with mocked retriever and mocked LLM
  - PII redactor (golden test set of inputs/outputs)
  - Cost calculator (token → USD)
- **Coverage target:** ≥80% on `app/agent/`, `app/rag/`, `app/memory/`, `app/services/`.

### 16.2 Integration tests with `httpx.AsyncClient` and `respx`
- **What:** spin up the FastAPI app in-process. Use `httpx.AsyncClient(transport=ASGITransport(app))` to hit endpoints. Use `respx` to mock `httpx` calls to OpenRouter — deterministic, no real spend, no flake.
- **Critical test:** the full graph run, end-to-end, against a mocked LLM, asserting the state transitions and final answer shape.

### 16.3 Agent evals
- **What:** write `eval/golden_conversations.jsonl` — 50+ multi-turn conversations with expected outcomes. Use `deepeval` for:
  - `FaithfulnessMetric` (no hallucination)
  - `ContextualRelevancyMetric` (RAG chunks actually used)
  - `ToolCorrectnessMetric` (right tool, right args)
  - `AnswerRelevancyMetric` (final answer addresses the question)
- **CI gate:** eval suite must pass ≥90% on PRs that touch `app/agent/` or `app/rag/`.

### 16.4 CI pipeline — update `.github/workflows/ci.yml`
- **What:** the existing CI file already runs lint, test, and security jobs. Update it to:
  1. Pin Python to 3.11 (the CI currently targets 3.13; align with the actual runtime)
  2. Replace `flake8`/`black` with `ruff check` and `ruff format --check`
  3. Add `mypy --strict` step
  4. Replace the placeholder scripts/validate_project.py and tests/run_all_tests.py with real `pytest -q --cov=app --cov-fail-under=80`
  5. Add `pip-audit` (CVE check on the dependency tree)
  6. Keep the existing Docker build step
  7. Add a CI badge to the README

### 16.5 Security scanning
- **What:** `bandit` for Python security issues (SQL injection, hard-coded passwords, weak crypto). `pip-audit` for known CVEs in deps. The existing CI already has Trivy for container scanning — keep that.

**Pattern:** Test pyramid · Eval-driven development · Supply-chain security.

**Library:** `pytest`, `pytest-asyncio`, `pytest-cov`, `respx`, `httpx`, `deepeval`, `bandit`, `pip-audit`, GitHub Actions.

**Acceptance:**
- `pytest` runs in <60 s in CI
- A PR that introduces a new tool must include an eval case for it
- A PR that introduces a new dep must pass `pip-audit`
- A PR that fails eval cannot be merged
- README shows a passing CI badge

---

## Step 17: Minimal production deploy scope

### 17.1 DO: `/readyz` endpoint
- **What:** extend the current `/health` to `/readyz` that pings Chroma and SQLite. Returns 503 if either is degraded. The endpoint is useful for Docker health checks and interview demos.
- **Add a `GET /health` that always returns 200** (liveness, no deps checked) and `GET /readyz` that checks dependencies (readiness).
- **Library:** FastAPI `@app.get(...)` — no new deps.

### 17.2 DO: Clean Dockerfile
- **What:** the current Dockerfile exists but pulls GPU packages on a CPU container (via `requirements.txt`). Phase A Step 0 strips the GPU deps. After that, verify the Dockerfile:
  - Install `torch` from the CPU-only index: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
  - Use `--no-cache-dir` to keep the image lean
  - Multi-stage build: one stage for dependencies, one for the app
  - Aim for <2 GB image (currently ~5 GB)

### 17.3 DO: `DECISIONS.md`
- **What:** create `DECISIONS.md` documenting:
  - **Why SQLite, not Redis/Postgres:** personal demo, zero-config, already in the stack. "For production, you'd swap SQLite for Redis (session) + Postgres (persistence)."
  - **Why no OTel/Loki/Prometheus/Grafana:** RAM budget on a $6 droplet. "Prometheus client is wired but the collector is not deployed. The design is ready; deploy with docker-compose when needed."
  - **Why no K8s:** personal service with 1 user. "Kubernetes would be absurd overkill; Docker Compose on a single VM is correct for this scale. Here's the K8s manifest design I'd use at 100x traffic."
  - **Why no Cohere Rerank:** paid API. "Local bge-reranker-base or no reranker for v1; Cohere Rerank v3 for v2 ($0.001/query)."
  - **Cost posture:** OpenRouter budget tracking, $200 Student Developer Pack credit, $4-6/month droplet.
  - **Existing CI file:** the CI already has lint/test/security jobs; describe what was updated.
- **Purpose:** This document turns every "not built" into a deliberate, defensible architectural decision that a recruiter can ask about.

### 17.4 DEFERRED ITEMS (all documented in DECISIONS.md)
The following items from the original Phase D are **deferred to v2** and must NOT be built in this phase:

| Original Step | Deferred Item | Why Deferred |
|---|---|---|
| 17.1 | PostgreSQL + Alembic migration | SQLite is adequate for a single-user demo. Postgres adds setup + connection pooling complexity. |
| 17.2 | Gunicorn with multiple Uvicorn workers | Single-user demo needs one process. Gunicorn + Nginx adds config surface with zero throughput benefit. |
| 17.3 | Kubernetes manifests | Absurd overkill for a single-droplet personal service. If the project ever needs K8s, the design is straightforward. |
| 17.5 | Secret store (Vault / K8s Secrets) | `docker-compose` env vars are fine for a personal service. Document the production upgrade path. |
| 17.6 | Backups (Postgres PITR, Chroma snapshots) | SQLite + Chroma on a single volume. A simple cron-based `tar` + `scp` to block storage is enough. Managed DB backups are v2. |

**Pattern:** Deploy the minimum viable service · Document the upgrade path · Let the interview conversation cover the deferred items.

**Library:** No new deps for this step. `DECISIONS.md` is prose.

**Acceptance:**
- `curl /readyz` returns 200 when Chroma + SQLite are available, 503 when either is missing
- `docker build` succeeds and produces an image <2 GB
- `DECISIONS.md` exists and covers all deferred items with enough depth for an interview discussion

---

## End-of-Phase Checklist

- [ ] `structlog` configured; PII redactor in the log pipeline
- [ ] `/metrics` returns Prometheus exposition format; required metrics present
- [ ] OTel/Loki/Prometheus collector deployment documented as v2 in DECISIONS.md
- [ ] `pytest` + `respx` + `httpx` test suite runs in CI; ≥80% coverage on core packages
- [ ] `eval/` golden set with ≥50 conversations; `deepeval` passes ≥90%
- [ ] CI workflow updated: ruff, mypy, pytest, deepeval, bandit, pip-audit, docker build
- [ ] CI badge displayed in README
- [ ] `/readyz` endpoint pings Chroma + SQLite
- [ ] Dockerfile cleaned up (multi-stage, CPU torch, no GPU packages, <2 GB)
- [ ] `DECISIONS.md` documenting all deferred items with enough depth for interview questions
- [ ] Existing `observability/prometheus.yml` and `loki-config.yml` updated or removed (they're stale configs from the full Phase D design)
- [ ] README title updated from "Agentic Conversational AI System" to something honest (e.g., "Conversational AI Agent — RAG + Tool-Calling")

---

## Final Note

The original Phase D (in `ai-agent-system-audit-report.md`) included full OpenTelemetry, Prometheus + Loki, Postgres + Alembic, Gunicorn + Nginx, and Kubernetes. None of those are wrong — they just belong at a different scale. The D-lite scope keeps the parts a recruiter can see and verify (tests passing, CI badge green, `/readyz` responding, clean Dockerfile) and defers the infrastructure that would burn $200 of Student Developer Pack credit on RAM with zero demo value.

The single most important document to come out of this phase is `DECISIONS.md`. A candidate who can say "I chose not to deploy Postgres because SQLite is adequate for a single-user demo, but here's exactly how I'd migrate — Alembic migration, connection pooling, `pool_pre_ping`" is more impressive than one who just installed Postgres because the textbook said so.
