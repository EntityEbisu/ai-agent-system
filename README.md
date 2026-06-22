# AI Agent System — E-Commerce Customer Support Chatbot

[![CI/CD Pipeline](https://github.com/EntityEbisu/ai-agent-system/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/EntityEbisu/ai-agent-system/actions/workflows/ci.yml)

## Overview

A small-scale **Conversational AI Agent** that simulates an e-commerce customer support assistant. Built with a focus on production-readiness — structured agent logic, RAG-backed knowledge retrieval, persistent sessions, observability, and CI.

Built across four phases:

| Phase | What it added |
|---|---|
| **A** — Correctness & Security | Trimmed deps, PII redaction, JWT auth + rate limiting, SQLite session store, error handling |
| **B** — Agent Rebuild | Typed AgentState, tool registry, ReAct + Plan-and-Execute loop via LangGraph |
| **C** — Memory & RAG | Three-tier memory (episodic + semantic + working), semantic chunking, citation enforcement |
| **D-lite** — Tests & Deploy | Structlog + Prometheus metrics, unit/integration tests, multi-stage Dockerfile, CI pipeline |

## Quick Links

- [Usage Guide](USAGE_GUIDE.md) — API reference, examples, curl commands
- [Testing Guide](TESTING_GUIDE.md) — Manual and automated test procedures
- [Architecture & Decisions](DECISIONS.md) — Trade-offs, deferrals, v2 design notes
- [Changelog](CHANGELOG.md) — Version history

## Stack

| Component | Choice | Reason |
|---|---|---|
| **API** | FastAPI | Async-native, auto-docs, streaming |
| **Agent Framework** | LangGraph + LangChain | ReAct loop, state persistence, tool integration |
| **Vector Store** | ChromaDB 1.5 | Local, free, persistent |
| **Embeddings** | HuggingFace (`all-MiniLM-L6-v2`) | Free, runs on CPU, ~1s cold start |
| **LLM Provider** | OpenRouter | Flexible pricing, 100+ models, OpenAI-compatible API |
| **Session Store** | SQLite + SQLAlchemy | Persistent, no server process needed, WAL mode |
| **Observability** | Structlog + Prometheus | Structured JSON logs + /metrics endpoint |
| **Frontend** | Streamlit | Interactive session explorer and data viewer |
| **CI** | GitHub Actions | pytest + lint on push |
| **Container** | Docker (multi-stage) | ~500 MB final image |

## Project Structure

```
ai-agent-system/
├── app/                    # Application root
│   ├── main.py             # FastAPI app, routes, lifecycle
│   ├── agent/
│   │   ├── state.py        # AgentState TypedDict
│   │   ├── memory.py       # Three-tier memory (episodic + semantic + working)
│   │   ├── router.py       # Intent classification and routing
│   │   └── workflow.py     # ReAct / Plan-and-Execute loop
│   ├── rag/
│   │   ├── pipeline.py     # RAG generation pipeline
│   │   ├── retriever.py    # Chroma retriever
│   │   ├── ingest.py       # Document ingestion
│   │   └── data_lifecycle.py # Lifecycle management (version, archive)
│   ├── tools/
│   │   └── ...             # Tool definitions with Pydantic schema
│   ├── services/
│   │   ├── llm.py          # LLM client
│   │   ├── observability.py # Structlog + Prometheus metrics
│   │   └── data_introspection.py
│   ├── data/
│   │   ├── models.py       # SQLAlchemy ORM models
│   │   └── session.py      # Session store with per-key locking
│   └── auth/
│       └── ...             # JWT auth + rate limiting
├── tests/                  # pytest suite
│   ├── test_api.py
│   ├── test_agent.py
│   └── test_rag.py
├── frontend/
│   └── streamlit_app.py    # Interactive UI
├── data/                   # Runtime data (gitignored)
│   ├── chroma_db/          # Persistent vector store
│   ├── sqlite/             # Session database
│   └── docs/               # Source documents for ingestion
├── observability/
│   └── README.md           # Observability stack docs
├── scripts/                # Dev utilities
├── Dockerfile              # Multi-stage build (~500 MB)
├── docker-compose.yml      # API + Chroma
└── requirements.txt        # Pinned dependencies
```

## Setup

### 1. Prerequisites

- Python 3.11+
- OpenRouter API key (or any OpenAI-compatible provider)

### 2. Clone & environment

```bash
git clone https://github.com/EntityEbisu/ai-agent-system.git
cd ai-agent-system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your OpenRouter API key
```

### 4. Run

```bash
# Start the API
uvicorn app.main:app --reload

# In another terminal, start the frontend
streamlit run frontend/streamlit_app.py
```

### 5. Verify

```bash
# Health check
curl http://localhost:8000/health

# Or run the test suite
pytest
```

## API Endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/chat` | Send a message to the agent | JWT |
| `GET` | `/health` | Health check | No |
| `GET` | `/readyz` | Readiness (includes Chroma check) | No |
| `GET` | `/metrics` | Prometheus metrics | No |
| `POST` | `/auth/token` | Obtain JWT token | No |

See [Usage Guide](USAGE_GUIDE.md) for detailed examples.

## Key Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Agent control | Deterministic ReAct loop (not autonomous LLM) | Predictable, auditable, secure for financial data |
| Session store | SQLite (not Redis) | Single-process demo — no server needed |
| Embeddings | HuggingFace (not OpenAI) | Free, local, no API key needed |
| LLM provider | OpenRouter | Flexible pricing, model-agnostic |
| Reranker | **Deferred (v2)** | BGE reranker added ~1 GB RAM — skip for demo budget |
| Container | Multi-stage Dockerfile | ~500 MB final image |

All trade-offs are documented in [DECISIONS.md](DECISIONS.md).

## License & Author

Nguyễn Trọng Minh — demo project for AI agent system evaluation.
