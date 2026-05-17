# module_usage_map.md

## Used Modules (Tier 1 – imported and executed at runtime)

- `app.main` – FastAPI entry point, startup, endpoints.
- `app.agent.router` – request routing, intent classification.
- `app.agent.workflow` – order‑status tool workflow.
- `app.agent.memory` – in‑memory session store.
- `app.agent.state` – default session state template.
- `app.rag.pipeline` – RAG handling (sync & streaming).
- `app.rag.retriever` – Chroma vector‑store retriever.
- `app.services.llm` – LLM wrapper and embeddings.
- `app.services.observability` – logging, metrics, Timer.
- `app.services.data_introspection` – session summary endpoint.
- `app.data.models` – SQLAlchemy models and DB init.
- `app.tools.order_status` – mock order‑status check.
- `frontend.streamlit_app` – optional UI (not part of API runtime).

## Unused Modules (present in repo but never imported/executed)

- `app/api/` – empty placeholder directory.
- `scripts/` – contains utility scripts not referenced by the application.
- `observability/grafana/` – Grafana dashboards (configuration only).
- `observability/loki-config.yml` – Loki config (not wired in code).
- `observability/prometheus.yml` – Prometheus config (exposed only via `/metrics`).
- `data/` – top‑level data folder (no runtime usage).

*Only modules that appear in the call‑graph (Tier 1) are considered *used*; imports that are never executed are listed as *unused*.*