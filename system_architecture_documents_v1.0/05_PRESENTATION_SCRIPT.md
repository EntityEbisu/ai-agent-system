# 05_PRESENTATION_SCRIPT.md

**5‑Minute Interview Presentation Script**

*All points are derived from the audited implementation artifacts (`00_ARCHITECTURE_MAP.md`, `01_IMPLEMENTATION_AUDIT.md`, `03_LANDMINES.md`). Only features that are **implemented** are described. Future work is clearly marked as such.*

---

### 1. Problem
**What to say:**
> "We needed a lightweight, interactive AI assistant that can answer user queries, demonstrate a tool workflow (order‑status), and showcase a Retrieval‑Augmented Generation (RAG) pipeline, all within a single FastAPI service."
**Potential follow‑up:** *"Why not use an existing chatbot platform?"*
**Best answer:** Emphasise control over the end‑to‑end flow, ability to instrument every step, and the demo purpose of illustrating architecture decisions.

---

### 2. Requirements
**What to say:**
> "Core functional requirements were:
> 1. HTTP API with health‑check and Prometheus metrics.
> 2. Session‑aware chat endpoint (`/chat`).
> 3. Intent‑driven workflow (order‑status tool).
> 4. RAG capability using a vector store and LLM.
> 5. Basic observability (logging, latency metrics)."
**Potential follow‑up:** *"What non‑functional requirements were considered?"*
**Best answer:** Mention low latency, simplicity for a demo, and the need for easy local execution.

---

### 3. Architecture
**What to say:**
> "The tier‑1 runtime graph (see `00_ARCHITECTURE_MAP.md`) is:
> FastAPI → Router → either the Workflow engine or the RAG pipeline → LLM/Retriever → SQLite persistence and Prometheus observability."
**Potential follow‑up:** *"Why FastAPI?"*
**Best answer:** Async‑first, automatic OpenAPI, and seamless integration with Pydantic models.

---

### 4. Routing Logic
**What to say:**
> "`app/agent/router.py` inspects the intent returned by the LLM. If the intent is `order_status` it delegates to `app/agent/workflow.py`; otherwise it calls the RAG pipeline (`app/rag/pipeline.py`)."
**Potential follow‑up:** *"How is intent classification performed?"*
**Best answer:** The LLM itself returns a structured intent; the router simply matches the string.

---

### 5. RAG Pipeline
**What to say:**
> "`app.rag.pipeline.handle_rag` retrieves relevant chunks from Chroma DB (in‑memory/SQLite) via `app.rag.retriever.get_retriever`, passes them to the LLM (`app.services.llm`), and streams the response back using an async generator."
**Potential follow‑up:** *"How are embeddings generated?"*
**Best answer:** `app.services.llm.get_embeddings` creates embeddings on‑the‑fly; they are not cached.

---

### 6. Workflow Engine
**What to say:**
> "When intent == `order_status`, `app.agent.workflow.start_tool_flow` orchestrates three phases – start, handle, execute – using the mock `app.tools.order_status` implementation. This demonstrates tool integration without external dependencies."
**Potential follow‑up:** *"Is the tool real?"*
**Best answer:** It is a mock used for interview purposes; a real HTTP client would replace it in production.

---

### 7. Memory Design
**What to say:**
> "Session state lives in a process‑local dictionary (`app.agent.memory`). It is created on first request and attached to the FastAPI request context."
**Potential follow‑up:** *"What happens on a crash?"*
**Best answer:** State is lost – a known limitation (see Landmines). Production would move this to Redis or DynamoDB.

---

### 8. Observability
**What to say:**
> "`app.services.observability` provides a `Timer` context manager for latency, logs via `init_logging`, and a Prometheus `/metrics` endpoint. Loki configuration exists but is not wired (see Landmines)."
**Potential follow‑up:** *"Why no tracing?"*
**Best answer:** Tracing was out of scope for the demo; it is planned for production.

---

### 9. Tradeoffs
**What to say:**
> "We chose in‑process memory and SQLite for simplicity and rapid iteration. The mock tool avoids external service calls, keeping the demo self‑contained."
**Potential follow‑up:** *"What are the risks?"*
**Best answer:** State loss, limited scalability, and lack of durability – all documented in the Landmines file.

---

### 10. Limitations
**What to say:**
> "* Runtime vs README mismatch – deployment scripts are placeholders.
> * No authentication/authorization.
> * Single‑process deployment limits horizontal scaling.
> * SQLite and Chroma DB are not production‑grade stores.
> * Observability lacks Loki integration and detailed metrics."
**Potential follow‑up:** *"Which limitation would you address first?"*
**Best answer:** Persist session state and move to a managed DB (PostgreSQL) to enable scaling and reliability.

---

### 11. Future Improvements
**What to say:**
> "Planned upgrades include:
> * External session store (Redis).
> * PostgreSQL for persistence.
> * Managed vector DB (Pinecone/Milvus).
> * Full CI/CD pipeline with GitHub Actions.
> * API Gateway + ECS/Lambda deployment on AWS.
> * OAuth2/JWT security and rate limiting.
> * Loki log aggregation and OpenTelemetry tracing."
**Potential follow‑up:** *"How would you prioritize these?"*
**Best answer:** Prioritise state persistence and security, then observability and scaling.

---

*End of script – each bullet can be spoken in roughly 30 seconds, fitting a 5‑minute slot.*
