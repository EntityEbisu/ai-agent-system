# Phase A — Stop the Bleeding (Week 1)

**Theme:** Correctness, security, packaging. Make the repo honest about what it is and stop the immediate foot-guns.

**Do NOT start Phase B until all of Phase A is green.** Building a real agent on top of a service that loses state on restart, leaks PII, and OOMs after 10k sessions will just give you a fancier broken thing.

---

## Step 0: Lock the runtime contract

**What:**
- Create `pyproject.toml` (PEP 621) declaring the package, Python 3.11 pin, and dev tooling.
- Add `requirements-dev.txt` for test/lint deps.
- Audit `requirements.txt`. The current 167-line file is mostly transitive deps from `langchain`/`transformers`/`torch` that the code does not import. Strip everything that is not actually used at runtime.
- In the Dockerfile, install the right torch wheel for the target arch: `pip install torch --index-url https://download.pytorch.org/whl/cpu`. The current requirements pull `nvidia-cudnn-cu13`, `nvidia-cublas`, `cuda-toolkit` (lines 17–19, 76–90) — these are GPU-only and have no business on a CPU container.

**Pattern:** Twelve-Factor App · Reproducible builds · Declared runtime contract.

**Library:** `pyproject.toml`, `ruff`, `mypy --strict`, `pre-commit`.

**Acceptance:** `pip install -e ".[dev]"` works on a clean machine in <2 min. `ruff check` and `mypy` both pass on a fresh checkout.

---

## Step 1: Fix the duplicate function and column/code mismatch

**What:**
- `app/data/models.py:89-102` defines `init_db` a second time. Delete it. Python silently rebinds the name; the first definition is dead code that signals copy-paste rot.
- `app/data/models.py:33` defines `context_type = Column(String(50), default="general")`. The only writer, `app/main.py::persist_message` (lines 44–70), never sets it. Either:
  - **Drop the column** (recommended if the value is not used for routing or analytics).
  - **Or populate it**: pass the resolved intent into `persist_message` and store it on `ConversationSession.context_type` as well as `Message.intent`.
- The query side (`data_introspection.py:31`, `streamlit_app.py:159`) assumes a meaningful value; align the two sides or both delete the field.

**Pattern:** DRY · Schema/code co-evolution · Single source of truth.

**Library:** `alembic` for schema migrations (introduce it now so future changes don't need another round of cleanup).

**Acceptance:** `grep -rn "context_type" app/` returns a consistent set of reads and writes. `init_db` is defined exactly once. `alembic check` is clean.

---

## Step 2: Stop blocking the event loop & stop reloading models per request

**What:**
- `app/rag/retriever.py::get_retriever` instantiates `HuggingFaceEmbeddings` (~80 MB) **on every request**. The model load takes 1–3 s the first time and is discarded when the function returns. Same for `Chroma(...)` SQLite open. Cache the singletons.
- `app/services/llm.py::get_llm` rebuilds the `ChatOpenAI` client per call. Cache it. Key the cache on `(model, temperature, streaming)` so config changes invalidate cleanly.
- `app/rag/pipeline.py:13` and `27` call `chain.invoke(...)` synchronously. Wrap any unavoidable blocking call in `asyncio.to_thread(...)`.
- Mark all FastAPI request handlers `async def`. Audit every `def` endpoint in `app/main.py` and convert; the ones that perform I/O (most of the introspection ones) are silently blocking the event loop today.

**Pattern:** Dependency injection · Async-first design · Cached singletons · Bounded resources.

**Library:** `functools.lru_cache` (or a manual `@cache` with a `threading.Lock` for the slow loaders), FastAPI `lifespan` context for one-time init at startup, `asyncio.to_thread`.

**Acceptance:** First request after process start completes in <500 ms (was multi-second). `wrk -t4 -c32 -d30s` against `/chat` shows no requests blocking others.

---

## Step 3: Replace the in-memory `dict` session store with a SQLite backend

**What:**
- `app/agent/memory.py` is 12 lines: `sessions: Dict[str, dict] = {}` with no lock, no eviction, no serialization, no persistence. The same `dict` reference is mutated concurrently by parallel requests for the same `session_id` — guaranteed race conditions.
- Move the store into the **existing SQLite database** (the same `conversations.db` used by `ConversationSession` and `Message`). Add a `session_state` table: `(session_id TEXT PK, state_json TEXT, updated_at TIMESTAMP)`. The state is serialized to JSON on write, deserialized on read.
- Use a per-session **`asyncio.Lock`** held in a module-level `dict[str, asyncio.Lock]` to prevent concurrent mutations. Evict stale locks on a timer.
- Keep the `TypedDict` (or Pydantic) shape and enforce it on serialize/deserialize.
- **Rationale:** This is a personal demo project serving one concurrent user. SQLite is already in the stack and avoids adding Redis as a dependency. The demo narrative can acknowledge "for production, you'd swap SQLite for Redis + TTL" in a DECISIONS.md document.

**Pattern:** Externalized state · Per-key locking · Minimal dependency footprint.

**Library:** `sqlite3` (already a dependency), `pydantic` v2 for the state schema, `asyncio.Lock`.

**Acceptance:** Killing the process loses nothing (state is in SQLite). Two concurrent `/chat` calls on the same `session_id` do not corrupt each other (write a regression test). No `redis` package added to dependencies.

---

## Step 4: Add authentication, rate limiting, and PII redaction

**What:**
- `app/main.py:88` instantiates `FastAPI(...)` with zero security. Add a JWT verification dependency (or `fastapi-users` if you want full registration flows) and require it on every endpoint except `/health` and `/readyz`. Populate `request.state.user_id`.
- **Session ownership check:** a session is owned by its `user_id`. `/api/v1/data/sessions/{session_id}` and `/api/v1/data/sessions` (lines 190, 202) must filter by `request.state.user_id`. Right now anyone can read any session.
- **Rate limit:** add `slowapi` middleware. 60 req/min per user, 10 req/min per IP for unauthenticated endpoints.
- **PII redaction:** `app/services/observability.py:67` logs `message_preview = message[:50]` to disk unredacted. The order-status flow puts `"John Smith"`, `"1234"`, `"1990-01-01"` into the log. Add a redactor (`presidio-analyzer` or a small regex pass) that masks names, SSN-shaped patterns, DOB-shaped patterns before they hit the file handler.
- **PII at rest:** `messages.content` in SQLite stores the raw PII unencrypted. For a real deployment, either (a) do not store user turns that contain PII — only store the tool's redacted output, or (b) encrypt the column. The `presidio` anonymizer covers (a).
- **HTTPS:** in production, terminate TLS at the proxy (Nginx, ALB, Caddy). The app should refuse non-localhost non-TLS connections via `Strict-Transport-Security` headers and a `pydantic-settings` guard.

**Pattern:** Defense-in-depth · Data minimization · Least privilege · Fail-secure.

**Library:** `pyjwt` (or `fastapi-users`), `slowapi`, `presidio-analyzer` + `presidio-anonymizer`, `pydantic-settings`.

**Acceptance:** `curl http://localhost:8000/api/v1/data/sessions` without a token returns 401. `curl -H "Authorization: Bearer $A" .../sessions/$B` returns 403 when `B` belongs to a different user. A request that contains an SSN-shaped string in the message produces a log line with `***-**-****` instead.

---

## Step 5: Path-traversal & input validation on lifecycle endpoints

**What:**
- `app/main.py:306-322` exposes `POST /api/v1/rag/ingest` with `file_path: str` taken straight from the client. The handler calls `RAGDataLifecycle.ingest_document(file_path, ...)` which opens the path server-side. `file_path="../../../../etc/passwd"` is accepted if the process has read access.
- Constrain `file_path` to a `Path` rooted at the configured docs directory (`data/docs/`):
  ```python
  root = Path(config.APIConfig.DOCS_DIR).resolve()
  target = (root / file_path).resolve()
  if not target.is_relative_to(root):
      raise HTTPException(400, "file_path must be under DOCS_DIR")
  ```
- Validate `tags: list[str]` length (e.g., max 20, each tag max 64 chars, alphanumeric + `-`).
- Add a `POST /api/v1/rag/upload` endpoint that accepts a `UploadFile` and writes it under `data/docs/` with a server-generated UUID name. **That is the only ingestion path.** Drop the path-as-string one.
- Audit every other endpoint that takes a path/string-from-client for the same issue. `data_introspection.py`, `data_lifecycle.py::list_documents` use safe paths; check the rest.

**Pattern:** Allow-list input validation · Server-generated identifiers · Treat all client input as hostile.

**Library:** `pathlib.Path.resolve().is_relative_to(...)`, `fastapi.UploadFile`.

**Acceptance:** `curl -d '{"file_path": "../../../etc/passwd", "session_id": "x", "message": "y"}' /api/v1/rag/ingest` returns 400. Direct `file_path` parameter is removed; only the upload endpoint remains.

---

## Step 6: Real error handling + graceful LLM failures

**What:**
- `app/services/llm.py:20-21` raises `ValueError("OPENROUTER_API_KEY must be set...")` if the key is missing. This bubbles to `app/main.py:180` and is yielded verbatim to the client as `{"error": "OPENROUTER_API_KEY must be set..."}`. **Internal config strings are leaking to the user.** Map to a user-safe message and log the original at ERROR.
- No retry/backoff for 429 rate-limits or 5xx from OpenRouter. `tenacity` is in `requirements.txt:142` and is not used anywhere. Wrap LLM and retriever calls in a retry policy: exponential backoff with jitter, max 3 attempts, max total 30 s.
- No timeout on LLM calls. An OpenRouter stall hangs the request indefinitely. Set a per-request deadline (e.g., 30 s) and surface a typed error on expiry.
- `retriever.invoke(query)` has no try/except. A missing Chroma directory raises `ValueError` from the underlying client; the raw exception string is yielded to the client. Catch and translate.
- `workflow.py:34, 42` returns "Invalid SSN" / "Invalid DOB" as plain strings. If `execute_tool` raises, the exception propagates unhandled. Wrap the whole `handle_tool_flow` body in try/except, log at ERROR, return a generic "Something went wrong. Please try again."
- Add a global FastAPI exception handler that returns RFC-7807 problem details and never leaks internals.

**Pattern:** Circuit breaker · Exponential backoff · Fail-soft · Error containment.

**Library:** `tenacity` (`retry`, `stop_after_attempt`, `wait_exponential_jitter`), `httpx.Timeout`, FastAPI exception handlers.

**Acceptance:** With `OPENROUTER_API_KEY` unset, `/chat` returns a friendly message and a structured `{"error_type": "config_error", "trace_id": "..."}` — no raw `ValueError` text. With a mocked 429-then-200 LLM, the request succeeds on the second attempt. With a mocked 60 s stall, the request fails at 30 s with a typed timeout error.

---

## End-of-Phase Checklist

- [ ] `pyproject.toml` exists, `ruff` + `mypy` + `pytest` pass
- [ ] `init_db` defined exactly once; `context_type` column consistent
- [ ] Embeddings, LLM client, retriever client are singletons; no per-request model load
- [ ] All handlers `async def`; no `def` doing I/O
- [ ] Session store backed by SQLite; per-key lock
- [ ] JWT auth on every endpoint except `/health` and `/readyz`; session ownership enforced
- [ ] `slowapi` rate limit configured
- [ ] PII redactor in logger; PII not stored in `messages.content`
- [ ] `/api/v1/rag/ingest` accepts only server-rooted paths; raw `file_path` parameter removed
- [ ] LLM/retriever calls wrapped in `tenacity` retry with timeout
- [ ] Global exception handler returns sanitized errors
- [ ] `/health` extended to `/readyz` that pings Redis (and Postgres if available)

When all of these are green, proceed to **Phase B** (`audit-phase-B.md`).
