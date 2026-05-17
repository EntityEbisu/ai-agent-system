# feature_matrix.md

| Feature | Claimed in README | Exists in Code | Wired in Runtime | Interview‑safe Claim |
|---------|-------------------|----------------|------------------|----------------------|
| API entrypoint | ✅ (README mentions FastAPI) | ✅ (`app/main.py`) | ✅ (`/chat`, `/health`, `/metrics`) | IMPLEMENTED |
| Agent routing | ✅ (README describes routing) | ✅ (`app/agent/router.py`) | ✅ (`handle_message`, `handle_message_stream`) | IMPLEMENTED |
| Workflow engine | ✅ (order‑status workflow) | ✅ (`app/agent/workflow.py`) | ✅ (invoked when intent == "order_status") | IMPLEMENTED |
| Memory | ✅ (session memory) | ✅ (`app/agent/memory.py`) | ✅ (used by `/chat` endpoint) | IMPLEMENTED |
| RAG | ✅ (RAG pipeline) | ✅ (`app/rag/pipeline.py`, `app/rag/retriever.py`) | ✅ (used for non‑tool intents) | IMPLEMENTED |
| Embeddings | ✅ (embeddings for vector store) | ✅ (`app/services/llm.py` provides `get_embeddings`) | ✅ (retriever loads embeddings) | IMPLEMENTED |
| Vector store | ✅ (Chroma DB) | ✅ (`app/rag/retriever.py`) | ✅ (retriever loads persisted DB) | IMPLEMENTED |
| Persistence | ✅ (SQLite DB) | ✅ (`app/data/models.py`) | ✅ (messages persisted in `/chat`) | IMPLEMENTED |
| Observability | ✅ (metrics, logging) | ✅ (`app/services/observability.py`) | ✅ (`/metrics`, logger usage) | IMPLEMENTED |
| Streaming | ✅ (streaming chat) | ✅ (`handle_message_stream`, `handle_rag_stream`) | ✅ (async generator yields chunks) | IMPLEMENTED |
| Deployment | ✅ (Dockerfile, docker‑compose) | ❌ (no code triggers deployment) | ❌ (not part of runtime) | PLANNED ONLY |
| CI/CD | ✅ (GitHub Actions badge) | ❌ (no CI scripts in repo) | ❌ (not executed at runtime) | PLANNED ONLY |