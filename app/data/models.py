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


class SessionState(Base):
    """Persistent session state store backed by SQLite.

    Stores serialized JSON state for each active conversation session.
    Managed by ``app.agent.memory`` via raw SQL for simplicity.
    """

    __tablename__ = "session_state"

    session_id = Column(String, primary_key=True)
    state_json = Column(Text, nullable=False)
    updated_at = Column(String, nullable=False)


class Order(Base):
    """Demo e-commerce order for the order-status tool."""

    __tablename__ = "orders"

    order_id = Column(String(36), primary_key=True)
    customer_name = Column(String(255), nullable=False)
    ssn_last4 = Column(String(4), nullable=False)
    dob = Column(String(10), nullable=False)  # YYYY-MM-DD
    status = Column(String(50), nullable=False)  # shipped | processing | delayed | delivered
    estimated_delivery = Column(String(10), nullable=True)
    items = Column(Text, nullable=True)  # JSON list of item names
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """Demo user profile for the customer-support chatbot."""

    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    shipping_address = Column(Text, nullable=True)  # JSON dict
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Seed data ──────────────────────────────────────────────────────

SEED_ORDERS: list[dict] = [
    {
        "order_id": "ORD-001",
        "customer_name": "John Smith",
        "ssn_last4": "1234",
        "dob": "1990-01-15",
        "status": "shipped",
        "estimated_delivery": "2026-06-25",
        "items": '["Wireless Headphones", "USB-C Hub"]',
    },
    {
        "order_id": "ORD-002",
        "customer_name": "John Smith",
        "ssn_last4": "1234",
        "dob": "1990-01-15",
        "status": "processing",
        "estimated_delivery": "2026-07-02",
        "items": '["Laptop Stand"]',
    },
    {
        "order_id": "ORD-003",
        "customer_name": "Jane Doe",
        "ssn_last4": "5678",
        "dob": "1985-08-22",
        "status": "delivered",
        "estimated_delivery": "2026-06-10",
        "items": '["Mechanical Keyboard", "Mouse Pad", "Monitor Arm"]',
    },
    {
        "order_id": "ORD-004",
        "customer_name": "Jane Doe",
        "ssn_last4": "5678",
        "dob": "1985-08-22",
        "status": "delayed",
        "estimated_delivery": "2026-07-05",
        "items": '["Webcam"]',
    },
    {
        "order_id": "ORD-005",
        "customer_name": "Bob Johnson",
        "ssn_last4": "9012",
        "dob": "1978-11-03",
        "status": "shipped",
        "estimated_delivery": "2026-06-28",
        "items": '["Smartphone Case", "Screen Protector", "Charging Cable"]',
    },
]

SEED_USERS: list[dict] = [
    {
        "user_id": "u1",
        "name": "John Smith",
        "email": "john.smith@example.com",
        "shipping_address": '{"street": "123 Main St", "city": "Portland", "state": "OR", "zip": "97201"}',
    },
    {
        "user_id": "u2",
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "shipping_address": '{"street": "456 Oak Ave", "city": "Austin", "state": "TX", "zip": "78701"}',
    },
    {
        "user_id": "u3",
        "name": "Bob Johnson",
        "email": "bob.j@example.com",
        "shipping_address": '{"street": "789 Pine Rd", "city": "Denver", "state": "CO", "zip": "80202"}',
    },
]


def seed_demo_data(database_url: str) -> None:
    """Insert demo orders and users if their tables are empty.

    Safe to call multiple times — checks row count before inserting.
    """
    from sqlalchemy import inspect as sa_inspect

    engine = create_engine(database_url, echo=False)

    # Only seed if tables exist and are empty
    inspector = sa_inspect(engine)
    if "orders" not in inspector.get_table_names():
        return
    if "users" not in inspector.get_table_names():
        return

    with engine.connect() as conn:
        from sqlalchemy import text

        order_count = conn.execute(text("SELECT COUNT(*) FROM orders")).scalar()
        if order_count == 0:
            for row in SEED_ORDERS:
                conn.execute(
                    text(
                        "INSERT INTO orders (order_id, customer_name, ssn_last4, dob, "
                        "status, estimated_delivery, items) "
                        "VALUES (:order_id, :customer_name, :ssn_last4, :dob, "
                        ":status, :estimated_delivery, :items)"
                    ),
                    row,
                )

        user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        if user_count == 0:
            for row in SEED_USERS:
                conn.execute(
                    text(
                        "INSERT INTO users (user_id, name, email, shipping_address) "
                        "VALUES (:user_id, :name, :email, :shipping_address)"
                    ),
                    row,
                )

        conn.commit()


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
    seed_demo_data(database_url)
    _session_factory = sessionmaker(bind=engine)
    return _session_factory, engine
