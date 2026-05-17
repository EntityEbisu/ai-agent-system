# 04_MOCK_INTERVIEW_LOG.md

**Mock Interview Log – Cloud Solution Architect Intern**

*This simulation is calibrated for an INTERN-level AI/Data Solution Architect interview. All candidate answers are derived solely from the verified implementation in the truth source files. No planned features are claimed as implemented.*

---

## Round 1 — Project Presentation Defense (5 questions)

### Question 1

**Interviewer Question:** Can you walk me through the problem this system was designed to solve and how you approached the requirements?

**Candidate Answer (likely realistic intern answer):** The system is an AI assistant that handles chat queries, either through a workflow for order status or using RAG for general questions. I built it with FastAPI for the API, used Chroma for vector storage, and SQLite for data. It streams responses and has basic metrics.

**Evaluation:**
- Technical correctness: High – aligns with core functionality.
- Clarity: Medium – covers basics but lacks depth on requirements.
- Confidence level: Medium – straightforward explanation.
- Intern-level maturity: Good – understands own implementation.

**Weaknesses:**
- Missing: Specific requirements like health checks, session awareness.
- Weakly explained: Why FastAPI or RAG was chosen.
- Could confuse: Vague on how it handles different intents.

**Stronger Answer:** The project implements a conversational AI assistant with two main capabilities: tool-based workflows for specific tasks like order status checks, and RAG for answering questions based on ingested documents. Key requirements included session-aware chat, streaming responses, basic observability, and a simple deployment setup. I chose FastAPI for its async capabilities and OpenAPI generation, Chroma DB for vector storage in the demo, and SQLite for persistence to keep it lightweight.

**Pressure Follow-up:** Why did you choose Chroma DB over other vector stores?

**Best Follow-up Answer:** For the demo, Chroma was simple to set up with in-memory storage and SQLite persistence, allowing quick iteration without external dependencies. In production, I'd consider managed options like Pinecone for scalability.

**Risk Level:** Medium

**Tag:** Presentation

### Question 2

**Interviewer Question:** How does the system determine whether to use the workflow engine or the RAG pipeline for a user message?

**Candidate Answer (likely realistic intern answer):** The router checks the intent from the LLM. If it's "order_status", it goes to the workflow; otherwise, it's RAG.

**Evaluation:**
- Technical correctness: High – matches router logic.
- Clarity: High – simple and direct.
- Confidence level: High – confident in the code.
- Intern-level maturity: Good – explains routing clearly.

**Weaknesses:**
- Missing: Details on how intent is extracted.
- Weakly explained: What happens in each path.
- Could confuse: Assumes interviewer knows the components.

**Stronger Answer:** In `app/agent/router.py`, the system first gets an intent classification from the LLM response. If the intent string matches "order_status", it delegates to the workflow engine in `app/agent/workflow.py`. For all other intents, it routes to the RAG pipeline in `app/rag/pipeline.py`, which retrieves relevant documents and generates a response.

**Pressure Follow-up:** What if the LLM returns an invalid intent?

**Best Follow-up Answer:** Currently, it defaults to RAG, but in production, I'd add validation to ensure only known intents are processed, perhaps with a fallback or error message.

**Risk Level:** Low

**Tag:** Architecture

### Question 3

**Interviewer Question:** Describe the RAG pipeline and how it retrieves information.

**Candidate Answer (likely realistic intern answer):** The RAG pipeline takes the user query, gets embeddings, searches Chroma DB for similar chunks, and passes them to the LLM to generate an answer. It streams the response back.

**Evaluation:**
- Technical correctness: High – accurate to implementation.
- Clarity: Medium – covers steps but skips details.
- Confidence level: Medium – knows the flow.
- Intern-level maturity: Good – understands retrieval process.

**Weaknesses:**
- Missing: Chunking strategy, overlap, or limitations.
- Weakly explained: How embeddings are used in retrieval.
- Could confuse: Doesn't mention hallucination prevention.

**Stronger Answer:** The RAG pipeline in `app/rag/pipeline.py` starts by generating embeddings for the user query using `app/services/llm.py`. It then queries Chroma DB via `app/rag/retriever.py` to find the top-k similar document chunks. These chunks are passed as context to the LLM, which generates a response. The system streams the output using an async generator to provide real-time feedback.

**Pressure Follow-up:** How do you prevent hallucinations in the RAG responses?

**Best Follow-up Answer:** By providing relevant context from retrieved chunks, the LLM is grounded in the data. However, there's no explicit hallucination detection; in production, I'd add relevance scoring or fact-checking.

**Risk Level:** Medium

**Tag:** RAG

### Question 4

**Interviewer Question:** What happens when a user starts a new chat session?

**Candidate Answer (likely realistic intern answer):** A new session is created in memory with an ID, and messages are stored in SQLite.

**Evaluation:**
- Technical correctness: High – sessions are created and persisted.
- Clarity: Medium – basic but accurate.
- Confidence level: High – familiar with session handling.
- Intern-level maturity: Good – knows persistence layer.

**Weaknesses:**
- Missing: Details on session lifecycle or state transitions.
- Weakly explained: How sessions are retrieved.
- Could confuse: Doesn't mention in-memory limitation.

**Stronger Answer:** When a new session is needed, `app/agent/memory.py` creates a session object with a unique ID and stores it in an in-process dictionary. Messages are persisted to SQLite using SQLAlchemy models in `app/data/models.py`. On subsequent requests, the session is retrieved by ID from the request context.

**Pressure Follow-up:** What if the server restarts during a session?

**Best Follow-up Answer:** The session state is lost since it's in-memory. That's a known limitation; production would use Redis for persistence.

**Risk Level:** Medium

**Tag:** Workflow

### Question 5

**Interviewer Question:** How are responses streamed to the user?

**Candidate Answer (likely realistic intern answer):** Using async generators in FastAPI, yielding NDJSON chunks for each token.

**Evaluation:**
- Technical correctness: High – matches streaming implementation.
- Clarity: High – direct explanation.
- Confidence level: High – understands async behavior.
- Intern-level maturity: Good – knows backend streaming.

**Weaknesses:**
- Missing: Why streaming is used or back-pressure.
- Weakly explained: Difference between workflow and RAG streaming.
- Could confuse: Assumes knowledge of NDJSON.

**Stronger Answer:** Both the workflow and RAG handlers use async generators (`handle_message_stream` and `handle_rag_stream`) to yield response chunks in NDJSON format. This allows real-time streaming of LLM tokens to the client, improving user experience for long responses.

**Pressure Follow-up:** What are the limitations of this streaming approach?

**Best Follow-up Answer:** No back-pressure handling, so if the client is slow, it could buffer. In production, I'd implement flow control or use SSE.

**Risk Level:** Low

**Tag:** API

---

## Round 2 — Architecture Understanding (5 questions)

### Question 6

**Interviewer Question:** Explain the separation of concerns in your architecture.

**Candidate Answer (likely realistic intern answer):** FastAPI handles the API, router decides the path, workflow or RAG does the work, and services handle LLM and persistence.

**Evaluation:**
- Technical correctness: High – reflects tier-1 graph.
- Clarity: Medium – lists components but not relationships.
- Confidence level: Medium – understands high-level structure.
- Intern-level maturity: Good – sees modularity.

**Weaknesses:**
- Missing: Details on how components interact.
- Weakly explained: Why this separation matters.
- Could confuse: Vague on runtime components.

**Stronger Answer:** The architecture follows a layered approach: FastAPI as the entry point with endpoints, a router for intent-based delegation, specialized pipelines (workflow for tools, RAG for retrieval), and shared services for LLM calls, persistence, and observability. This keeps concerns separated, making it easier to test and modify individual parts.

**Pressure Follow-up:** How does the router ensure modularity?

**Best Follow-up Answer:** By using simple string matching on intent, it decouples the decision logic from the execution, allowing new intents to be added without changing the router.

**Risk Level:** Low

**Tag:** Architecture

### Question 7

**Interviewer Question:** What are the active runtime components when the system is running?

**Candidate Answer (likely realistic intern answer):** FastAPI server, Chroma DB, SQLite, and the LLM service.

**Evaluation:**
- Technical correctness: High – core components.
- Clarity: High – lists them clearly.
- Confidence level: High – knows what's running.
- Intern-level maturity: Good – understands runtime.

**Weaknesses:**
- Missing: In-memory session dict, observability.
- Weakly explained: How they interact.
- Could confuse: Doesn't specify if LLM is external.

**Stronger Answer:** At runtime, the FastAPI app runs with endpoints, the router and pipelines are loaded, Chroma DB holds vectors, SQLite persists data, and the LLM (via API) generates responses. Observability collects metrics in the background.

**Pressure Follow-up:** Which component could be a bottleneck?

**Best Follow-up Answer:** The LLM API calls, as they are synchronous and could delay responses. I'd add async batching or caching.

**Risk Level:** Medium

**Tag:** Architecture

### Question 8

**Interviewer Question:** How does the request lifecycle work from HTTP request to response?

**Candidate Answer (likely realistic intern answer):** Request comes in, session is checked or created, intent is routed, either workflow or RAG processes it, response is streamed, and data is saved.

**Evaluation:**
- Technical correctness: High – matches architecture map.
- Clarity: Medium – steps are there but brief.
- Confidence level: Medium – knows the flow.
- Intern-level maturity: Good – explains lifecycle.

**Weaknesses:**
- Missing: Logging, metrics collection.
- Weakly explained: Persistence timing.
- Could confuse: Skips error handling.

**Stronger Answer:** A request hits `/chat`, FastAPI extracts session ID, creates or retrieves session, logs the request, routes based on intent, executes the pipeline (workflow or RAG), streams the response while persisting messages, and updates metrics.

**Pressure Follow-up:** What happens if routing fails?

**Best Follow-up Answer:** It defaults to RAG, but ideally, I'd add error handling to return a helpful message if intent is unrecognized.

**Risk Level:** Low

**Tag:** Architecture

### Question 9

**Interviewer Question:** Why did you choose FastAPI for the backend?

**Candidate Answer (likely realistic intern answer):** It's async, fast, and good for APIs with automatic docs.

**Evaluation:**
- Technical correctness: High – standard reasons.
- Clarity: High – concise.
- Confidence level: High – knows the choice.
- Intern-level maturity: Good – understands framework benefits.

**Weaknesses:**
- Missing: Specific integrations like Pydantic.
- Weakly explained: Compared to alternatives.
- Could confuse: Doesn't tie to project needs.

**Stronger Answer:** FastAPI was chosen for its async-first design, which supports streaming responses, automatic OpenAPI generation for docs, and seamless Pydantic model validation, making it ideal for a chat API with structured data.

**Pressure Follow-up:** How does async help in this system?

**Best Follow-up Answer:** It allows non-blocking I/O for LLM calls and streaming, preventing the server from hanging on long responses.

**Risk Level:** Low

**Tag:** API

### Question 10

**Interviewer Question:** Describe the state transitions in the workflow engine.

**Candidate Answer (likely realistic intern answer):** It starts with start phase, then handle, then execute the tool.

**Evaluation:**
- Technical correctness: High – matches workflow phases.
- Clarity: Medium – basic phases.
- Confidence level: Medium – understands workflow.
- Intern-level maturity: Good – knows the logic.

**Weaknesses:**
- Missing: What each phase does.
- Weakly explained: Validation or missing data.
- Could confuse: Doesn't explain deterministic flow.

**Stronger Answer:** The workflow in `app/agent/workflow.py` has three phases: start (initialize tool), handle (process input), and execute (run tool). It's deterministic, with state transitions based on the tool's requirements.

**Pressure Follow-up:** How does it handle missing data?

**Best Follow-up Answer:** Currently, it assumes data is present; in production, I'd add validation to check for required fields before proceeding.

**Risk Level:** Medium

**Tag:** Workflow

---

## Round 3 — RAG Fundamentals (5 questions)

### Question 11

**Interviewer Question:** How are documents chunked for the vector store?

**Candidate Answer (likely realistic intern answer):** Documents are split into chunks with some overlap, but I didn't implement the chunking myself; it's in the ingest pipeline.

**Evaluation:**
- Technical correctness: Medium – acknowledges chunking exists.
- Clarity: Low – vague on details.
- Confidence level: Low – unsure of implementation.
- Intern-level maturity: Fair – knows it's important.

**Weaknesses:**
- Missing: Specific chunk size, overlap strategy.
- Weakly explained: Why chunking matters.
- Could confuse: Doesn't know the code details.

**Stronger Answer:** In `app/rag/ingest.py`, documents are chunked into fixed-size pieces with overlap to preserve context across boundaries. This ensures that relevant information isn't split awkwardly during retrieval.

**Pressure Follow-up:** What chunk size did you use and why?

**Best Follow-up Answer:** I used a default size with overlap, but honestly, I didn't tune it; in production, I'd experiment with sizes based on document types for better retrieval.

**Risk Level:** High

**Tag:** RAG

### Question 12

**Interviewer Question:** Explain the role of embeddings in retrieval.

**Candidate Answer (likely realistic intern answer):** Embeddings turn text into vectors, and we find similar vectors in the store to get relevant chunks.

**Evaluation:**
- Technical correctness: High – basic understanding.
- Clarity: High – simple explanation.
- Confidence level: High – knows the concept.
- Intern-level maturity: Good – understands fundamentals.

**Weaknesses:**
- Missing: How similarity is measured.
- Weakly explained: Embedding generation process.
- Could confuse: Doesn't mention limitations.

**Stronger Answer:** Embeddings convert text queries and document chunks into high-dimensional vectors using `app/services/llm.py`. Retrieval finds the most similar vectors in Chroma DB using cosine similarity, returning relevant context for the LLM.

**Pressure Follow-up:** What are the limitations of this retrieval method?

**Best Follow-up Answer:** It can miss semantic matches if embeddings aren't perfect, and there's no reranking. Also, it's not cached, so repeated queries regenerate embeddings.

**Risk Level:** Medium

**Tag:** RAG

### Question 13

**Interviewer Question:** How does the system prevent hallucinations in RAG responses?

**Candidate Answer (likely realistic intern answer):** By providing context from retrieved documents, the LLM sticks to the facts.

**Evaluation:**
- Technical correctness: Medium – partial understanding.
- Clarity: Medium – basic idea.
- Confidence level: Medium – believes it works.
- Intern-level maturity: Fair – knows the concept.

**Weaknesses:**
- Missing: No explicit prevention mechanisms.
- Weakly explained: What happens if context is irrelevant.
- Could confuse: Overstates the prevention.

**Stronger Answer:** Hallucinations are mitigated by grounding the LLM in retrieved document chunks, but there's no additional fact-checking. The system relies on the quality of retrieval to provide accurate context.

**Pressure Follow-up:** What if the retrieved chunks are irrelevant?

**Best Follow-up Answer:** The LLM might still hallucinate. I'd add relevance scoring or a fallback to general knowledge, but currently, it's not handled.

**Risk Level:** High

**Tag:** RAG

### Question 14

**Interviewer Question:** What are the retrieval limitations in your implementation?

**Candidate Answer (likely realistic intern answer):** Chroma is in-memory, so no persistence, and retrieval might not be perfect.

**Evaluation:**
- Technical correctness: High – knows Chroma limits.
- Clarity: Medium – mentions basics.
- Confidence level: Medium – aware of issues.
- Intern-level maturity: Good – understands tradeoffs.

**Weaknesses:**
- Missing: Specifics like scaling or concurrency.
- Weakly explained: How it affects users.
- Could confuse: Doesn't tie to RAG specifically.

**Stronger Answer:** The vector store is Chroma with SQLite persistence, which lacks durability and scaling for high loads. Retrieval is basic similarity search without advanced features like reranking or hybrid search.

**Pressure Follow-up:** How would you improve retrieval accuracy?

**Best Follow-up Answer:** Add reranking with a cross-encoder model or hybrid BM25 + vector search to combine keyword and semantic matching.

**Risk Level:** Medium

**Tag:** RAG

### Question 15

**Interviewer Question:** How are embeddings generated and stored?

**Candidate Answer (likely realistic intern answer):** Using the LLM service to get embeddings, stored in Chroma DB.

**Evaluation:**
- Technical correctness: High – accurate.
- Clarity: High – straightforward.
- Confidence level: High – knows the process.
- Intern-level maturity: Good – understands storage.

**Weaknesses:**
- Missing: When embeddings are generated (on-the-fly).
- Weakly explained: Storage format.
- Could confuse: Doesn't mention caching absence.

**Stronger Answer:** Embeddings are generated on-demand via `app/services/llm.py` for queries and during ingest for documents. They are stored in Chroma DB's vector index for efficient similarity search.

**Pressure Follow-up:** Why not cache embeddings?

**Best Follow-up Answer:** To keep it simple for the demo; in production, I'd cache query embeddings in Redis to reduce API calls and latency.

**Risk Level:** Low

**Tag:** RAG

---

## Round 4 — Workflow Logic (4 questions)

### Question 16

**Interviewer Question:** Describe the deterministic workflow for the order status tool.

**Candidate Answer (likely realistic intern answer):** It starts the tool, handles the input, and executes to get the status.

**Evaluation:**
- Technical correctness: High – phases are correct.
- Clarity: Medium – lists phases.
- Confidence level: Medium – knows the flow.
- Intern-level maturity: Good – understands determinism.

**Weaknesses:**
- Missing: What each phase entails.
- Weakly explained: State transitions.
- Could confuse: Doesn't explain why deterministic.

**Stronger Answer:** The workflow is deterministic: start phase initializes the tool context, handle phase processes user input and validates data, execute phase runs the mock tool to simulate fetching order status.

**Pressure Follow-up:** What makes it deterministic?

**Best Follow-up Answer:** Each phase has defined inputs and outputs, with no branching based on external state; it's linear for this simple tool.

**Risk Level:** Low

**Tag:** Workflow

### Question 17

**Interviewer Question:** How does the workflow handle validation?

**Candidate Answer (likely realistic intern answer):** It checks if the input is valid, but it's basic.

**Evaluation:**
- Technical correctness: Low – validation is minimal.
- Clarity: Low – vague.
- Confidence level: Low – unsure.
- Intern-level maturity: Fair – knows it's needed.

**Weaknesses:**
- Missing: Specific validation logic.
- Weakly explained: What happens on failure.
- Could confuse: Doesn't admit limitations.

**Stronger Answer:** Validation is implicit in the handle phase, assuming required data is present. There's no explicit schema validation; it proceeds if the tool can run.

**Pressure Follow-up:** What if required data is missing?

**Best Follow-up Answer:** It might fail or return an error. I'd add input validation with Pydantic models to catch missing fields early.

**Risk Level:** High

**Tag:** Workflow

### Question 18

**Interviewer Question:** Explain state transitions in the workflow.

**Candidate Answer (likely realistic intern answer):** From start to handle to execute, based on the tool's needs.

**Evaluation:**
- Technical correctness: High – correct sequence.
- Clarity: Medium – basic transitions.
- Confidence level: Medium – understands sequence.
- Intern-level maturity: Good – knows the logic.

**Weaknesses:**
- Missing: Conditions for transitions.
- Weakly explained: Persistence of state.
- Could confuse: Doesn't tie to session.

**Stronger Answer:** State transitions are hardcoded: after start, move to handle for input processing, then to execute for tool run. State is held in the session memory.

**Pressure Follow-up:** How is state persisted across requests?

**Best Follow-up Answer:** In the in-memory dict, so it's lost on restart. For multi-step workflows, I'd need persistent state.

**Risk Level:** Medium

**Tag:** Workflow

### Question 19

**Interviewer Question:** How does the system handle missing data in workflows?

**Candidate Answer (likely realistic intern answer):** It assumes data is there; if not, it might error.

**Evaluation:**
- Technical correctness: High – honest about limitations.
- Clarity: Medium – admits issue.
- Confidence level: Medium – aware of gap.
- Intern-level maturity: Good – understands need for handling.

**Weaknesses:**
- Missing: Specific error handling.
- Weakly explained: User experience.
- Could confuse: Doesn't propose fixes.

**Stronger Answer:** Currently, missing data causes the workflow to fail. There's no graceful handling; in production, I'd add checks and prompts for missing information.

**Pressure Follow-up:** What would you do for missing order ID?

**Best Follow-up Answer:** Prompt the user to provide it, or check the session history for previous mentions.

**Risk Level:** Medium

**Tag:** Workflow

---

## Round 5 — API and Backend Fundamentals (4 questions)

### Question 20

**Interviewer Question:** Why choose FastAPI over other frameworks?

**Candidate Answer (likely realistic intern answer):** It's fast, async, and has good docs.

**Evaluation:**
- Technical correctness: High – standard reasons.
- Clarity: High – concise.
- Confidence level: High – knows choice.
- Intern-level maturity: Good – understands benefits.

**Weaknesses:**
- Missing: Specific to project (streaming).
- Weakly explained: Compared to Flask/Django.
- Could confuse: Doesn't tie to async needs.

**Stronger Answer:** FastAPI's async support is perfect for streaming LLM responses, and its automatic API docs help with development. It's more modern than Flask for this use case.

**Pressure Follow-up:** How does async improve performance?

**Best Follow-up Answer:** It allows concurrent handling of multiple requests without blocking on I/O, crucial for API calls to the LLM.

**Risk Level:** Low

**Tag:** API

### Question 21

**Interviewer Question:** Explain the async behavior in your endpoints.

**Candidate Answer (likely realistic intern answer):** Endpoints are async functions, yielding responses.

**Evaluation:**
- Technical correctness: High – correct.
- Clarity: Medium – basic.
- Confidence level: Medium – understands async.
- Intern-level maturity: Good – knows async.

**Weaknesses:**
- Missing: Why async for streaming.
- Weakly explained: Difference from sync.
- Could confuse: Doesn't explain generators.

**Stronger Answer:** The `/chat` endpoint is an async function that uses async generators to stream NDJSON responses, allowing non-blocking I/O for LLM interactions.

**Pressure Follow-up:** What are the downsides of async here?

**Best Follow-up Answer:** Debugging can be harder, and if not careful, it can lead to blocking calls. Also, no back-pressure.

**Risk Level:** Low

**Tag:** API

### Question 22

**Interviewer Question:** How are endpoints designed for the chat API?

**Candidate Answer (likely realistic intern answer):** POST to /chat with session ID and message, returns streamed response.

**Evaluation:**
- Technical correctness: High – matches design.
- Clarity: High – clear design.
- Confidence level: High – knows the API.
- Intern-level maturity: Good – understands design.

**Weaknesses:**
- Missing: Other endpoints like /health.
- Weakly explained: Request/response format.
- Could confuse: Doesn't mention error handling.

**Stronger Answer:** The `/chat` endpoint accepts JSON with session_id and message, routes internally, and streams NDJSON tokens. `/health` and `/metrics` are simple GETs for monitoring.

**Pressure Follow-up:** How do you handle API errors?

**Best Follow-up Answer:** Basic FastAPI error responses; in production, I'd add custom exception handlers for better user messages.

**Risk Level:** Low

**Tag:** API

### Question 23

**Interviewer Question:** Describe the streaming implementation.

**Candidate Answer (likely realistic intern answer):** Using async generators to yield chunks.

**Evaluation:**
- Technical correctness: High – accurate.
- Clarity: Medium – basic.
- Confidence level: High – knows it.
- Intern-level maturity: Good – understands streaming.

**Weaknesses:**
- Missing: NDJSON format.
- Weakly explained: Client handling.
- Could confuse: Doesn't mention flow control.

**Stronger Answer:** Streaming uses `StreamingResponse` with async generators that yield NDJSON objects for each token, enabling real-time updates in the client.

**Pressure Follow-up:** What if the stream is interrupted?

**Best Follow-up Answer:** The client might miss parts; I'd add sequence numbers or resumable streams, but currently, it's not handled.

**Risk Level:** Medium

**Tag:** API

---

## Round 6 — Observability and Persistence Awareness (3 questions)

### Question 24

**Interviewer Question:** What observability is implemented?

**Candidate Answer (likely realistic intern answer):** Basic logging and Prometheus metrics for latency.

**Evaluation:**
- Technical correctness: High – matches implementation.
- Clarity: High – accurate.
- Confidence level: High – knows what's there.
- Intern-level maturity: Good – aware of basics.

**Weaknesses:**
- Missing: Loki not wired.
- Weakly explained: How metrics are used.
- Could confuse: Doesn't mention limitations.

**Stronger Answer:** Logging via `init_logging`, a `Timer` for request latency, and a `/metrics` endpoint for Prometheus. Loki config exists but isn't integrated.

**Pressure Follow-up:** Why not wire Loki?

**Best Follow-up Answer:** It was out of scope for the demo; in production, I'd add the exporter for centralized logging.

**Risk Level:** Low

**Tag:** Observability

### Question 25

**Interviewer Question:** What is not integrated in observability?

**Candidate Answer (likely realistic intern answer):** Loki for logs, and no tracing.

**Evaluation:**
- Technical correctness: High – honest.
- Clarity: High – clear.
- Confidence level: Medium – knows gaps.
- Intern-level maturity: Good – understands what's missing.

**Weaknesses:**
- Missing: Detailed metrics.
- Weakly explained: Why it matters.
- Could confuse: Doesn't tie to production.

**Stronger Answer:** Loki is configured but not wired, no tracing with OpenTelemetry, and metrics are basic without histograms or error counters.

**Pressure Follow-up:** How would you add tracing?

**Best Follow-up Answer:** Integrate OpenTelemetry SDK to instrument requests and export to Jaeger or CloudWatch.

**Risk Level:** Low

**Tag:** Observability

### Question 26

**Interviewer Question:** Why does persistence matter for sessions?

**Candidate Answer (likely realistic intern answer):** So sessions survive restarts and can be shared.

**Evaluation:**
- Technical correctness: High – correct.
- Clarity: Medium – basic.
- Confidence level: Medium – understands importance.
- Intern-level maturity: Good – knows the need.

**Weaknesses:**
- Missing: Specific risks.
- Weakly explained: Impact on users.
- Could confuse: Doesn't mention current in-memory.

**Stronger Answer:** Persistence ensures session state isn't lost on server restarts, allowing continuity and potential horizontal scaling across instances.

**Pressure Follow-up:** What are the risks of in-memory persistence?

**Best Follow-up Answer:** Data loss on crashes, no fault tolerance. That's why I'd move to Redis in production.

**Risk Level:** Medium

**Tag:** Persistence

---

## Round 7 — Security Awareness (4 questions)

### Question 27

**Interviewer Question:** How is SSN handling secured?

**Candidate Answer (likely realistic intern answer):** It's not; the mock tool doesn't handle real SSNs.

**Evaluation:**
- Technical correctness: High – honest.
- Clarity: High – clear.
- Confidence level: High – knows it's mock.
- Intern-level maturity: Good – aware of security.

**Weaknesses:**
- Missing: General PII handling.
- Weakly explained: Why it matters.
- Could confuse: Doesn't discuss logging.

**Stronger Answer:** The order status tool is mock, so no real SSN handling. In production, I'd ensure SSNs are encrypted at rest and masked in logs.

**Pressure Follow-up:** How would you secure PII in logs?

**Best Follow-up Answer:** Use structured logging with PII fields excluded or hashed, and ensure logs are encrypted.

**Risk Level:** Low

**Tag:** Security

### Question 28

**Interviewer Question:** What input validation is in place?

**Candidate Answer (likely realistic intern answer):** Basic Pydantic models for requests.

**Evaluation:**
- Technical correctness: High – uses Pydantic.
- Clarity: Medium – mentions it.
- Confidence level: Medium – knows validation.
- Intern-level maturity: Good – understands basics.

**Weaknesses:**
- Missing: Specific validations.
- Weakly explained: Against what threats.
- Could confuse: Doesn't mention SQL injection.

**Stronger Answer:** FastAPI uses Pydantic for automatic validation of JSON inputs, preventing malformed requests. No additional sanitization for SQL injection since using SQLAlchemy.

**Pressure Follow-up:** How do you prevent injection attacks?

**Best Follow-up Answer:** SQLAlchemy's ORM prevents SQL injection, but for LLM prompts, I'd add input sanitization to avoid prompt injection.

**Risk Level:** Medium

**Tag:** Security

### Question 29

**Interviewer Question:** What PII exposure risks exist?

**Candidate Answer (likely realistic intern answer):** Messages might contain PII, logged in plain text.

**Evaluation:**
- Technical correctness: High – aware of risk.
- Clarity: Medium – identifies issue.
- Confidence level: Medium – concerned.
- Intern-level maturity: Good – thinks about privacy.

**Weaknesses:**
- Missing: Session data exposure.
- Weakly explained: Mitigation.
- Could confuse: Doesn't specify logs.

**Stronger Answer:** User messages could include PII, which is stored in SQLite and logged. No masking or encryption currently.

**Pressure Follow-up:** How would you mitigate PII exposure?

**Best Follow-up Answer:** Implement PII detection and masking in logs, encrypt sensitive data in DB, and add access controls.

**Risk Level:** Medium

**Tag:** Security

### Question 30

**Interviewer Question:** How is logging handled safely?

**Candidate Answer (likely realistic intern answer):** Basic logging, but might log sensitive data.

**Evaluation:**
- Technical correctness: Medium – admits risk.
- Clarity: Low – vague.
- Confidence level: Low – unsure.
- Intern-level maturity: Fair – knows it's an issue.

**Weaknesses:**
- Missing: Specific safety measures.
- Weakly explained: What to log.
- Could confuse: Doesn't mention Loki.

**Stronger Answer:** Logging uses `init_logging` to stdout, but doesn't filter sensitive data. In production, I'd add log levels and PII scrubbing.

**Pressure Follow-up:** What sensitive data might be logged?

**Best Follow-up Answer:** User messages with potential PII like names or SSNs. I'd exclude or hash them.

**Risk Level:** High

**Tag:** Security

---

## Round 8 — Basic Cloud Production Thinking (4 questions)

### Question 31

**Interviewer Question:** How would you deploy this to AWS?

**Candidate Answer (likely realistic intern answer):** Use ECS or Lambda with API Gateway.

**Evaluation:**
- Technical correctness: High – basic options.
- Clarity: Medium – mentions services.
- Confidence level: Medium – knows basics.
- Intern-level maturity: Good – understands deployment.

**Weaknesses:**
- Missing: Specific steps.
- Weakly explained: Why those services.
- Could confuse: Doesn't tie to architecture.

**Stronger Answer:** Containerize with Docker, push to ECR, deploy to ECS Fargate behind API Gateway for scaling and security.

**Pressure Follow-up:** Why ECS over Lambda?

**Best Follow-up Answer:** ECS gives more control over the container environment, better for long-running processes like this.

**Risk Level:** Low

**Tag:** Cloud

### Question 32

**Interviewer Question:** How to handle session scaling in the cloud?

**Candidate Answer (likely realistic intern answer):** Move sessions to Redis for shared state.

**Evaluation:**
- Technical correctness: High – correct fix.
- Clarity: High – direct.
- Confidence level: High – knows the issue.
- Intern-level maturity: Good – understands scaling.

**Weaknesses:**
- Missing: Redis setup.
- Weakly explained: How it scales.
- Could confuse: Doesn't mention persistence.

**Stronger Answer:** Replace in-memory sessions with ElastiCache Redis, allowing multiple instances to share state and survive restarts.

**Pressure Follow-up:** What Redis configuration for sessions?

**Best Follow-up Answer:** Use TTL for expiration, cluster mode for high availability, and encryption for data.

**Risk Level:** Low

**Tag:** Scalability

### Question 33

**Interviewer Question:** What persistent storage would you use?

**Candidate Answer (likely realistic intern answer):** RDS for PostgreSQL instead of SQLite.

**Evaluation:**
- Technical correctness: High – standard choice.
- Clarity: High – clear.
- Confidence level: High – knows upgrade.
- Intern-level maturity: Good – understands persistence.

**Weaknesses:**
- Missing: Migration steps.
- Weakly explained: Why PostgreSQL.
- Could confuse: Doesn't mention backups.

**Stronger Answer:** Migrate to Amazon RDS PostgreSQL for ACID compliance, backups, and concurrent access, replacing SQLite.

**Pressure Follow-up:** How to migrate data?

**Best Follow-up Answer:** Export SQLite dump, create RDS schema with Alembic, import data, and update connection strings.

**Risk Level:** Low

**Tag:** Persistence

### Question 34

**Interviewer Question:** How to set up cloud observability?

**Candidate Answer (likely realistic intern answer):** Use CloudWatch for metrics and logs.

**Evaluation:**
- Technical correctness: High – AWS native.
- Clarity: Medium – basic.
- Confidence level: Medium – knows CloudWatch.
- Intern-level maturity: Good – understands monitoring.

**Weaknesses:**
- Missing: Integration details.
- Weakly explained: From current setup.
- Could confuse: Doesn't mention Loki.

**Stronger Answer:** Replace Prometheus with CloudWatch custom metrics, send logs to CloudWatch Logs, and set up alarms for latency and errors.

**Pressure Follow-up:** How to integrate with existing code?

**Best Follow-up Answer:** Use boto3 to emit metrics instead of Prometheus client, and configure logging to CloudWatch.

**Risk Level:** Low

**Tag:** Cloud

---

## Performance Summary

**Strongest Areas**
- Understanding of core implementation (routing, RAG, workflow)
- Awareness of limitations and tradeoffs
- Basic cloud deployment knowledge

**Weakest Areas**
- RAG details (chunking, hallucination prevention)
- Security implementations (PII handling, input validation)
- Advanced API features (error handling, streaming robustness)

**Most Dangerous Questions**
- Q11 (Chunking details) – Exposed lack of tuning knowledge
- Q13 (Hallucination prevention) – Weak on mitigation
- Q30 (Logging safety) – High risk of admitting gaps

**Most Likely Real Interview Questions**
- Q1 (Problem framing)
- Q2 (Routing logic)
- Q6 (Architecture separation)
- Q12 (Embeddings role)

**Topics to Review Tonight**
- RAG chunking strategies and overlap
- Security best practices for PII
- Async streaming limitations
- Cloud service integrations

**Top 10 Questions to Memorize**
1. Q1 – Project problem and requirements
2. Q2 – Routing decision logic
3. Q3 – RAG pipeline description
4. Q6 – Separation of concerns
5. Q12 – Embeddings in retrieval
6. Q16 – Workflow determinism
7. Q20 – FastAPI choice
8. Q24 – Implemented observability
9. Q27 – SSN security
10. Q31 – AWS deployment basics

**Top 5 Weaknesses to Fix Before Interview**
1. Deepen RAG fundamentals (chunking, retrieval limits)
2. Strengthen security awareness (PII, logging)
3. Improve workflow validation details
4. Add API error handling knowledge
5. Practice cloud migration explanations

**Best Talking Points to Emphasize**
- Built the system end-to-end as intern
- Clear understanding of design choices and tradeoffs
- Honest about limitations with production fixes
- Practical cloud thinking without over-engineering

**Best Honest Limitations to Admit**
- Mock tool implementation
- In-memory session state
- Basic observability
- No authentication layer
- SQLite for persistence</content>
<parameter name="filePath">/home/tminh/ai-agent-system/interview-prep/04_MOCK_INTERVIEW_LOG.md