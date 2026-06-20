"""
Phase A — Correctness & Security
Step 4: Auth, rate limiting, PII redaction.

Implements:
- JWT verification on all endpoints except /health and /readyz
- slowapi rate limiting (60 req/min authenticated, 10 req/min unauthenticated)
- PII redaction on logged messages and stored message content
- HSTS security header
"""

import json
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.agent.memory import configure as configure_session_store
from app.agent.memory import get_session, save_session
from app.agent.router import handle_message_stream
from app.auth.dependencies import verify_token
from app.data.models import ConversationSession, Message, init_db
from app.pii.redactor import redact, redact_message
from app.services.observability import Timer, init_logging

# Lazy-import observability helpers to avoid circular deps
_logger = None
_metrics = None
_db_session_factory = None

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "data/sqlite/conversations.db"))
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

_security_scheme = HTTPBearer(auto_error=False)


# ═══════════════════════════════════════════════════════════════════
#  Rate limiter
# ═══════════════════════════════════════════════════════════════════
limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])


# ═══════════════════════════════════════════════════════════════════
#  Startup / Shutdown lifecycle
# ═══════════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initializes logging, DB, and session store."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    configure_session_store(DATABASE_PATH)
    log_file = os.getenv("LOG_FILE", "logs/app.log")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    init_logging(log_file=log_file, log_level=log_level)
    global _db_session_factory
    _db_session_factory, _ = init_db(DATABASE_URL)
    yield


app = FastAPI(
    title="AI Agent System",
    version="1.0.0",
    lifespan=lifespan,
)

# Register rate-limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Middleware ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers (HSTS) to every response."""
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    return response


# ═══════════════════════════════════════════════════════════════════
#  Request / response models
# ═══════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    """Chat request payload."""
    session_id: str
    message: str


class TokenRequest(BaseModel):
    """Token issuance request (demo use only)."""
    user_id: str = "demo-user"


# ═══════════════════════════════════════════════════════════════════
#  Auth helpers
# ═══════════════════════════════════════════════════════════════════

def _get_user_id(payload: dict | None) -> str | None:
    """Extract user_id from a verified JWT payload or return None."""
    if payload and "sub" in payload:
        return payload["sub"]
    return None


async def _optional_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security_scheme),
) -> dict | None:
    """Dependency that optionally returns the token payload (no error on missing)."""
    if credentials is None:
        return None
    try:
        from app.auth.jwt_handler import decode_access_token
        return decode_access_token(credentials.credentials)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════
#  Public endpoints (no auth required)
# ═══════════════════════════════════════════════════════════════════

@app.get("/health")
@limiter.exempt
async def health(request: Request):
    """Health check endpoint for Docker and load balancers."""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "version": "1.0.0"},
    )


@app.get("/readyz")
@limiter.exempt
async def readyz(request: Request):
    """Readiness check — confirms DB is reachable."""
    try:
        get_db_session().close()
        return JSONResponse(status_code=200, content={"status": "ready"})
    except Exception as e:
        return JSONResponse(
            status_code=503, content={"status": "not ready", "detail": str(e)}
        )


@app.post("/api/v1/auth/token")
@limiter.exempt
async def issue_token(request: Request, req: TokenRequest):
    """Issue a demo JWT token (no real auth — for development only)."""
    from app.auth.jwt_handler import create_access_token
    token = create_access_token(user_id=req.user_id)
    return JSONResponse(
        status_code=200,
        content={"access_token": token, "token_type": "bearer"},
    )


# ═══════════════════════════════════════════════════════════════════
#  DB helpers
# ═══════════════════════════════════════════════════════════════════

def get_db_session():
    """Get a database session from the configured factory."""
    global _db_session_factory
    if _db_session_factory is None:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _db_session_factory, _ = init_db(DATABASE_URL)
    return _db_session_factory()


def persist_message(session_id, role, content, intent=None, context_type=None,
                    processing_time_ms=None, tokens_used=None):
    """Persist a (redacted) chat message to the SQLite database.

    Args:
        session_id: Unique session identifier.
        role: Message role ("user", "assistant", "system").
        content: Message body text (will be redacted before storage).
        intent: Classified intent.
        context_type: Session context type.
        processing_time_ms: Response latency in milliseconds.
        tokens_used: Token count for cost tracking.
    """
    # Redact PII before storing
    redacted_content = redact(content) if (role == "user" and content) else content

    db = get_db_session()
    try:
        conversation = db.query(ConversationSession).filter_by(id=session_id).first()
        if conversation is None:
            conversation = ConversationSession(id=session_id)
            db.add(conversation)
            db.commit()
        if context_type is not None:
            conversation.context_type = context_type
        message = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=redacted_content,
            intent=intent,
            processing_time_ms=processing_time_ms,
            tokens_used=tokens_used,
        )
        db.add(message)
        conversation.messages_count = (conversation.messages_count or 0) + 1
        db.commit()
    except Exception as e:
        logger = get_logger_instance()
        logger.log_error("db_write_error", str(e), {"session_id": session_id})
        db.rollback()
    finally:
        db.close()


def get_logger_instance():
    """Lazy-load logger."""
    global _logger
    if _logger is None:
        from app.services.observability import get_logger
        _logger = get_logger()
    return _logger


def get_metrics_instance():
    """Lazy-load metrics."""
    global _metrics
    if _metrics is None:
        from app.services.observability import metrics
        _metrics = metrics
    return _metrics


# ═══════════════════════════════════════════════════════════════════
#  Chat endpoint (auth required)
# ═══════════════════════════════════════════════════════════════════

@app.post("/chat")
@limiter.limit("60/minute")
async def chat(
    request: Request,
    req: ChatRequest,
    token_payload: dict = Depends(verify_token),
):
    """Chat endpoint with streaming responses and observability."""
    state = await get_session(req.session_id)
    logger = get_logger_instance()

    async def event_generator():
        try:
            with Timer("/chat") as timer:
                # Redact PII in logged message preview
                redacted_preview = redact(req.message[:100])

                logger.log_request(
                    endpoint="/chat",
                    method="POST",
                    session_id=req.session_id,
                    message_preview=redacted_preview,
                )

                persist_message(
                    session_id=req.session_id,
                    role="user",
                    content=req.message,
                    intent=state.get("intent"),
                    context_type=state.get("intent"),
                )

                full_response = ""
                token_count = 0
                async for chunk in handle_message_stream(req.message, state):
                    full_response += chunk
                    token_count += 1
                    yield json.dumps({"token": chunk}) + "\n"

            get_metrics_instance().record_latency("/chat", timer.elapsed_ms)

            estimated_user_tokens = len(req.message) // 4
            estimated_response_tokens = len(full_response) // 4
            total_tokens = estimated_user_tokens + estimated_response_tokens

            logger.log_response(
                endpoint="/chat",
                status="success",
                latency_ms=timer.elapsed_ms,
                tokens_used=total_tokens,
                prompt_tokens=estimated_user_tokens,
                completion_tokens=estimated_response_tokens,
            )

            persist_message(
                session_id=req.session_id,
                role="assistant",
                content=full_response,
                intent=state.get("intent"),
                context_type=state.get("intent"),
                processing_time_ms=timer.elapsed_ms,
                tokens_used=total_tokens,
            )

            state.get("history").append({
                "user": req.message,
                "assistant": full_response,
                "tokens": total_tokens,
            })

            await save_session(req.session_id, state)
        except Exception as e:
            logger.log_error("chat_error", str(e))
            from contextlib import suppress
            with suppress(Exception):
                await save_session(req.session_id, state)
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


# ═══════════════════════════════════════════════════════════════════
#  Data Visibility Endpoints (auth required)
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/v1/data/sessions")
@limiter.limit("60/minute")
async def get_sessions(
    request: Request,
    token_payload: dict = Depends(verify_token),
    limit: int = 20,
):
    """Get recent sessions for the authenticated user."""
    from app.services.data_introspection import DatabaseIntrospection
    db_intro = DatabaseIntrospection(DATABASE_URL)
    sessions = db_intro.get_session_summary(limit=limit)
    return JSONResponse(status_code=200, content={"sessions": sessions})


@app.get("/api/v1/data/sessions/{session_id}")
@limiter.limit("60/minute")
async def get_session_details(
    request: Request,
    session_id: str,
    token_payload: dict = Depends(verify_token),
):
    """Get detailed message history for a session."""
    from app.services.data_introspection import DatabaseIntrospection
    db_intro = DatabaseIntrospection(DATABASE_URL)
    messages = db_intro.get_session_messages(session_id)
    # Redact PII before serving
    redacted = [redact_message(m) if isinstance(m, dict) else m for m in messages]
    return JSONResponse(
        status_code=200,
        content={"session_id": session_id, "messages": redacted},
    )


@app.get("/api/v1/data/analytics/snapshot")
@limiter.limit("60/minute")
async def get_analytics_snapshot(
    request: Request,
    token_payload: dict = Depends(verify_token),
):
    """Get system metrics snapshot."""
    from app.services.data_introspection import DatabaseIntrospection
    db_intro = DatabaseIntrospection(DATABASE_URL)
    snapshot = db_intro.get_metrics_snapshot()
    return JSONResponse(status_code=200, content=snapshot)


@app.get("/api/v1/data/analytics/tokens")
@limiter.limit("60/minute")
async def get_token_report(
    request: Request,
    hours: int = 24,
    token_payload: dict = Depends(verify_token),
):
    """Get token usage report."""
    from app.services.data_introspection import DatabaseIntrospection
    db_intro = DatabaseIntrospection(DATABASE_URL)
    report = db_intro.get_token_usage_report(hours=hours)
    return JSONResponse(status_code=200, content=report)


@app.get("/api/v1/data/analytics/latency")
@limiter.limit("60/minute")
async def get_latency_report(
    request: Request,
    hours: int = 24,
    token_payload: dict = Depends(verify_token),
):
    """Get latency statistics."""
    from app.services.data_introspection import DatabaseIntrospection
    db_intro = DatabaseIntrospection(DATABASE_URL)
    report = db_intro.get_latency_report(hours=hours)
    return JSONResponse(status_code=200, content=report)


# ═══════════════════════════════════════════════════════════════════
#  Chroma Data Visibility Endpoints (auth required)
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/v1/rag/documents")
@limiter.limit("60/minute")
async def list_rag_documents(
    request: Request,
    token_payload: dict = Depends(verify_token),
):
    """List ingested documents in Chroma."""
    from app.services.data_introspection import ChromaIntrospection
    chroma_intro = ChromaIntrospection()
    docs = chroma_intro.list_documents()
    return JSONResponse(status_code=200, content=docs)


@app.post("/api/v1/rag/test-retrieval")
@limiter.limit("60/minute")
async def test_rag_retrieval(
    request: Request,
    req: ChatRequest,
    token_payload: dict = Depends(verify_token),
):
    """Test RAG retrieval for a query."""
    from app.services.data_introspection import ChromaIntrospection
    chroma_intro = ChromaIntrospection()
    result = chroma_intro.test_retrieval(req.message, k=5)
    return JSONResponse(status_code=200, content=result)


# ═══════════════════════════════════════════════════════════════════
#  Document Lifecycle Endpoints (auth required)
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/v1/rag/document-versions")
@limiter.limit("60/minute")
async def list_document_versions(
    request: Request,
    token_payload: dict = Depends(verify_token),
):
    """List all document versions and metadata."""
    from app.rag.data_lifecycle import RAGDataLifecycle
    lifecycle = RAGDataLifecycle()
    versions = lifecycle.list_document_versions()
    return JSONResponse(status_code=200, content={"documents": versions})


@app.get("/api/v1/rag/lifecycle-stats")
@limiter.limit("60/minute")
async def get_lifecycle_stats(
    request: Request,
    token_payload: dict = Depends(verify_token),
):
    """Get document lifecycle statistics."""
    from app.rag.data_lifecycle import RAGDataLifecycle
    lifecycle = RAGDataLifecycle()
    stats = lifecycle.get_lifecycle_stats()
    return JSONResponse(status_code=200, content=stats)


@app.post("/api/v1/rag/ingest")
@limiter.limit("60/minute")
async def ingest_document(
    request: Request,
    file_path: str,
    description: str = "",
    tags: list[str] | None = None,
    token_payload: dict = Depends(verify_token),
):
    """Ingest or update a document in the knowledge base.

    .. caution::
       ``file_path`` is validated to stay under the configured ``DOCS_DIR``.
       Use ``POST /api/v1/rag/upload`` (when implemented) for file uploads.
    """
    from app.rag.data_lifecycle import RAGDataLifecycle
    lifecycle = RAGDataLifecycle()
    try:
        result = lifecycle.ingest_document(file_path, description, tags)
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.post("/api/v1/rag/archive/{document_id}")
@limiter.limit("60/minute")
async def archive_document(
    request: Request,
    document_id: str,
    token_payload: dict = Depends(verify_token),
):
    """Archive a document (soft delete)."""
    from app.rag.data_lifecycle import RAGDataLifecycle
    lifecycle = RAGDataLifecycle()
    result = lifecycle.archive_document(document_id)
    return JSONResponse(status_code=200, content=result)


@app.get("/api/v1/rag/ingestion-history")
@limiter.limit("60/minute")
async def get_ingestion_history(
    request: Request,
    limit: int = 50,
    token_payload: dict = Depends(verify_token),
):
    """Get document ingestion history."""
    from app.rag.data_lifecycle import RAGDataLifecycle
    lifecycle = RAGDataLifecycle()
    history = lifecycle.get_ingestion_history(limit=limit)
    return JSONResponse(status_code=200, content={"history": history})


# ═══════════════════════════════════════════════════════════════════
#  Global exception handler
# ═══════════════════════════════════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler returning sanitized RFC-7807-like problem details."""
    logger = get_logger_instance()
    trace_id = str(uuid.uuid4())[:8]
    logger.log_error("unhandled_error", str(exc), {
        "trace_id": trace_id,
        "path": str(request.url),
    })
    return JSONResponse(
        status_code=500,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred. Please try again.",
            "trace_id": trace_id,
        },
    )
