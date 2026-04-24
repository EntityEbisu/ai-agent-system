import json
import os
import uuid
from pathlib import Path
from typing import List
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from app.agent.router import handle_message, handle_message_stream
from app.agent.memory import get_session
from app.data.models import init_db, ConversationSession, Message
from app.services.observability import init_logging, Timer

# Lazy import observability to avoid circular dependencies
_logger = None
_metrics = None
_db_session_factory = None

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "data/sqlite/conversations.db"))
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


def startup_event():
    """Initialize logging and database on startup."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_file = os.getenv("LOG_FILE", "logs/app.log")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    init_logging(log_file=log_file, log_level=log_level)
    global _db_session_factory
    _db_session_factory, _ = init_db(DATABASE_URL)


def get_db_session():
    """Get a database session from the configured factory."""
    global _db_session_factory
    if _db_session_factory is None:
        # Fallback initialization for testing or direct imports
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _db_session_factory, _ = init_db(DATABASE_URL)
    return _db_session_factory()


def persist_message(session_id: str, role: str, content: str, intent: str = None, processing_time_ms: float = None, tokens_used: int = None):
    """Persist a chat message to the SQLite database."""
    db = get_db_session()
    try:
        conversation = db.query(ConversationSession).filter_by(id=session_id).first()
        if conversation is None:
            conversation = ConversationSession(id=session_id)
            db.add(conversation)
            db.commit()
        message = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
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

app = FastAPI(title="AI Agent System", version="1.0.0")
app.on_event("startup")(startup_event)

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.get("/health")
async def health():
    """Health check endpoint for Docker and load balancers."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "version": "1.0.0"
        }
    )

@app.get("/metrics")
async def get_metrics():
    """Get system metrics (Level 300 - E2)."""
    metrics = get_metrics_instance()
    return JSONResponse(
        status_code=200,
        content=metrics.get_summary()
    )

@app.post("/chat")
async def chat(req: ChatRequest):
    """Chat endpoint with streaming responses and observability."""
    state = get_session(req.session_id)
    logger = get_logger_instance()
    
    async def event_generator():
        try:
            with Timer("/chat") as timer:
                # Log incoming request
                logger.log_request(
                    endpoint="/chat",
                    method="POST",
                    session_id=req.session_id,
                    message_preview=req.message
                )

                persist_message(
                    session_id=req.session_id,
                    role="user",
                    content=req.message,
                    intent=state.get("intent")
                )

                full_response = ""
                token_count = 0
                async for chunk in handle_message_stream(req.message, state):
                    full_response += chunk
                    token_count += 1  # Approximate token count (each chunk ~= 1 token)
                    yield json.dumps({"token": chunk}) + "\n"

            # Record metrics
            get_metrics_instance().record_latency("/chat", timer.elapsed_ms)

            # Estimate total tokens (user message + response)
            # Rough estimation: 1 token per 4 characters
            estimated_user_tokens = len(req.message) // 4
            estimated_response_tokens = len(full_response) // 4
            total_tokens = estimated_user_tokens + estimated_response_tokens

            # Log response with token counts
            logger.log_response(
                endpoint="/chat",
                status="success",
                latency_ms=timer.elapsed_ms,
                tokens_used=total_tokens,
                prompt_tokens=estimated_user_tokens,
                completion_tokens=estimated_response_tokens
            )

            persist_message(
                session_id=req.session_id,
                role="assistant",
                content=full_response,
                intent=state.get("intent"),
                processing_time_ms=timer.elapsed_ms,
                tokens_used=total_tokens
            )

            state["history"].append({
                "user": req.message,
                "assistant": full_response,
                "tokens": total_tokens
            })
        except Exception as e:
            logger.log_error("chat_error", str(e))
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


# =====================================================
# Data Visibility Endpoints (Level 300)
# =====================================================

@app.get("/api/v1/data/sessions")
async def get_sessions(limit: int = 20):
    """Get recent sessions with metadata."""
    from app.services.data_introspection import DatabaseIntrospection
    db_intro = DatabaseIntrospection(DATABASE_URL)
    sessions = db_intro.get_session_summary(limit=limit)
    return JSONResponse(
        status_code=200,
        content={"sessions": sessions}
    )


@app.get("/api/v1/data/sessions/{session_id}")
async def get_session_details(session_id: str):
    """Get detailed message history for a session."""
    from app.services.data_introspection import DatabaseIntrospection
    db_intro = DatabaseIntrospection(DATABASE_URL)
    messages = db_intro.get_session_messages(session_id)
    return JSONResponse(
        status_code=200,
        content={"session_id": session_id, "messages": messages}
    )


@app.get("/api/v1/data/analytics/snapshot")
async def get_analytics_snapshot():
    """Get system metrics snapshot."""
    from app.services.data_introspection import DatabaseIntrospection
    db_intro = DatabaseIntrospection(DATABASE_URL)
    snapshot = db_intro.get_metrics_snapshot()
    return JSONResponse(
        status_code=200,
        content=snapshot
    )


@app.get("/api/v1/data/analytics/tokens")
async def get_token_report(hours: int = 24):
    """Get token usage report."""
    from app.services.data_introspection import DatabaseIntrospection
    db_intro = DatabaseIntrospection(DATABASE_URL)
    report = db_intro.get_token_usage_report(hours=hours)
    return JSONResponse(
        status_code=200,
        content=report
    )


@app.get("/api/v1/data/analytics/latency")
async def get_latency_report(hours: int = 24):
    """Get latency statistics."""
    from app.services.data_introspection import DatabaseIntrospection
    db_intro = DatabaseIntrospection(DATABASE_URL)
    report = db_intro.get_latency_report(hours=hours)
    return JSONResponse(
        status_code=200,
        content=report
    )


# =====================================================
# Chroma Data Visibility Endpoints
# =====================================================

@app.get("/api/v1/rag/documents")
async def list_rag_documents():
    """List ingested documents in Chroma."""
    from app.services.data_introspection import ChromaIntrospection
    chroma_intro = ChromaIntrospection()
    docs = chroma_intro.list_documents()
    return JSONResponse(
        status_code=200,
        content=docs
    )


@app.post("/api/v1/rag/test-retrieval")
async def test_rag_retrieval(req: ChatRequest):
    """Test RAG retrieval for a query."""
    from app.services.data_introspection import ChromaIntrospection
    chroma_intro = ChromaIntrospection()
    result = chroma_intro.test_retrieval(req.message, k=5)
    return JSONResponse(
        status_code=200,
        content=result
    )


# =====================================================
# Document Lifecycle Endpoints (Level 300)
# =====================================================

@app.get("/api/v1/rag/document-versions")
async def list_document_versions():
    """List all document versions and metadata."""
    from app.rag.data_lifecycle import RAGDataLifecycle
    lifecycle = RAGDataLifecycle()
    versions = lifecycle.list_document_versions()
    return JSONResponse(
        status_code=200,
        content={"documents": versions}
    )


@app.get("/api/v1/rag/lifecycle-stats")
async def get_lifecycle_stats():
    """Get document lifecycle statistics."""
    from app.rag.data_lifecycle import RAGDataLifecycle
    lifecycle = RAGDataLifecycle()
    stats = lifecycle.get_lifecycle_stats()
    return JSONResponse(
        status_code=200,
        content=stats
    )


@app.post("/api/v1/rag/ingest")
async def ingest_document(file_path: str, description: str = "", tags: List[str] = None):
    """Ingest or update a document in the knowledge base."""
    from app.rag.data_lifecycle import RAGDataLifecycle
    
    lifecycle = RAGDataLifecycle()
    try:
        result = lifecycle.ingest_document(file_path, description, tags)
        return JSONResponse(
            status_code=200,
            content=result
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )


@app.post("/api/v1/rag/archive/{document_id}")
async def archive_document(document_id: str):
    """Archive a document (soft delete)."""
    from app.rag.data_lifecycle import RAGDataLifecycle
    lifecycle = RAGDataLifecycle()
    result = lifecycle.archive_document(document_id)
    return JSONResponse(
        status_code=200,
        content=result
    )


@app.get("/api/v1/rag/ingestion-history")
async def get_ingestion_history(limit: int = 50):
    """Get document ingestion history."""
    from app.rag.data_lifecycle import RAGDataLifecycle
    lifecycle = RAGDataLifecycle()
    history = lifecycle.get_ingestion_history(limit=limit)
    return JSONResponse(
        status_code=200,
        content={"history": history}
    )