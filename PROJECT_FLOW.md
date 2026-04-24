# Project Flow: Data, Logical, and Structural Diagrams

## 1. Data Flow

```
User Input
   ↓
Streamlit Frontend
   ↓ POST /chat
FastAPI Backend
   ↓
Intent Classification (router.py)
   ├── order_status
   │      ↓
   │      Tool Workflow (workflow.py)
   │      ↓
   │      Mock tool execution (order_status.py)
   │      ↓
   │      Response
   │
   └── rag
          ↓
          RAG Retriever (retriever.py)
          ↓
          Document context assembly
          ↓
          LLM generation (llm.py)
          ↓
          Streaming response

Backend Observability
   ├── logs/app.log
   ├── /metrics endpoint
   └── SQLite persistence (data/sqlite/conversations.db)

Frontend Explorer
   ├── session records
   ├── stored messages
   ├── RAG document list
   └── application logs
```

## 2. Logical Flow

```
User asks a question or requests order status
   ↓
Request arrives at /chat
   ↓
Load or create session state by session_id
   ↓
Classify intent:
   - if order status → start or continue workflow
   - else → run RAG retrieval
   ↓
Execute handler
   - tool workflow returns a guided response
   - RAG handler retrieves docs and streams LLM output
   ↓
Persist user request and assistant response to SQLite
   ↓
Record latency metric and log response event
   ↓
Stream tokens back to the frontend
   ↓
Frontend displays chat + data explorer updates
```

## 3. Project Structure

```
ai-agent-system/
│
├── app/
│   ├── main.py                  # FastAPI backend + observability + persistence
│   ├── agent/
│   │   ├── router.py            # Intent routing and message handler
│   │   ├── memory.py            # Session state management
│   │   └── workflow.py          # Order status workflow logic
│   ├── rag/
│   │   ├── pipeline.py          # RAG generation and streaming
│   │   └── retriever.py         # Chroma retriever
│   ├── data/
│   │   └── models.py            # SQLite ORM models and init helper
│   ├── services/
│   │   └── observability.py     # Logging and metrics collector
│   └── tools/
│       └── order_status.py      # Mock order status tool
│
├── frontend/
│   └── streamlit_app.py         # Streamlit UI and data explorer
│
├── data/
│   ├── docs/                    # Documents for RAG ingestion
│   └── sqlite/                  # SQLite database file
│
├── scripts/
│   ├── setup_db.py              # Initialize SQLite schema
│   ├── validate_project.py      # Validation/test script
│
├── TESTING_GUIDE.md             # Detailed test instructions
├── TESTING_CHECKLIST.md         # Interview/test checklist
├── PROJECT_FLOW.md              # This file
├── README.md                    # Project overview and quick start
└── project_briefing.md          # Assignment alignment and status
```

## 4. Current Alignment Summary

- Level 100: Core RAG + order workflow and multi-turn conversation → implemented.
- Level 200: FastAPI, streaming endpoint, frontend UI, health/metrics endpoints, Docker-ready design → implemented.
- Level 300: SQLite schema, observability, metrics collector, logging, persistence-ready architecture → implemented.
- Frontend explorer: data and log visibility for sessions, RAG documents, and application logs → added.

## 5. Notes

- The current implementation now persists chat messages to SQLite and exposes a simple Streamlit data explorer.
- The metrics endpoint now records actual `/chat` latency values instead of zero.
- Full diagramming in Figma/Drawio can be created from this text-based representation.
