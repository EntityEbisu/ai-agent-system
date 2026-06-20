"""
Data models for conversation persistence (Level 300).

This module defines SQLAlchemy ORM models for storing:
- Conversation sessions
- Messages (user & assistant)
- Tool execution records
- Token usage tracking

Models support multi-turn interactions and enable retrieval of past conversations.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class ConversationSession(Base):
    """Represents a conversation session (e.g., chat thread)."""

    __tablename__ = "conversation_sessions"

    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(255), nullable=True, index=True)  # Optional: tie to user
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)  # When session ended (if explicitly ended)

    # Metadata
    context_type = Column(String(50), default="general")  # e.g., "order_status", "faq", "general"
    messages_count = Column(Integer, default=0)  # Denormalized count for quick stats

    # Relations
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_session_created", "created_at"),
        Index("idx_session_user", "user_id"),
    )


class Message(Base):
    """Represents a single message in a conversation."""

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True)  # UUID
    session_id = Column(
        String(36), ForeignKey("conversation_sessions.id"), nullable=False, index=True
    )
    role = Column(String(20), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)  # Message body
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Metadata
    tokens_used = Column(Integer, nullable=True)  # Token count for LLM cost tracking
    processing_time_ms = Column(Float, nullable=True)  # Latency in milliseconds

    # Optional: routing information
    intent = Column(String(50), nullable=True)  # e.g., "rag", "workflow", "fallback"
    rag_query = Column(Boolean, default=False)  # Was this a RAG query?
    rag_relevant_chunks = Column(Integer, nullable=True)  # Number of chunks retrieved

    # Relations
    session = relationship("ConversationSession", back_populates="messages")

    __table_args__ = (
        Index("idx_message_session", "session_id"),
        Index("idx_message_created", "created_at"),
    )


# Database initialization helper
def init_db(database_url: str) -> sessionmaker:
    """
    Initialize database and create tables.

    Args:
        database_url: SQLAlchemy database URL (e.g., "sqlite:///data/sqlite/conversations.db")

    Returns:
        sessionmaker: Factory for creating database sessions
    """
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    _session_factory = sessionmaker(bind=engine)
    return _session_factory, engine
