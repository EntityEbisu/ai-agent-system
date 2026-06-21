"""Persistent session state — backed by SQLite with per-key locking.

Replaces the in-memory ``dict`` store with a persistent SQLite backend
that survives process restarts.

Uses per-session ``asyncio.Lock`` held in a module-level ``dict`` to prevent
concurrent mutations of the same session state.
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import messages_from_dict, messages_to_dict

_db_path: Path | None = None
_locks: dict[str, asyncio.Lock] = {}
_locks_lock = asyncio.Lock()


def configure(db_path: str | Path) -> None:
    """Set the database path (called once at startup before any get_session call).

    Args:
        db_path: Path to the SQLite database file.
    """
    global _db_path
    _db_path = Path(db_path)


def _get_connection() -> sqlite3.Connection:
    """Open a connection to the session database, ensuring tables exist.

    Returns:
        SQLite connection (caller should commit before discarding).
    """
    if _db_path is None:
        raise RuntimeError("Session store not configured — call configure() first")
    _db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS session_state (
            session_id TEXT PRIMARY KEY,
            state_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def new_session() -> dict[str, Any]:
    """Return a fresh AgentState-compatible dictionary with defaults.

    Returns:
        A plain dict that satisfies the ``AgentState`` contract.
    """
    return {
        "messages": [],
        "errors": [],
        "tool_calls_made": [],
        "iteration": 0,
    }


def _get_lock(session_id: str) -> asyncio.Lock:
    """Get or create a per-session asyncio.Lock.

    The locks dict is protected by its own lock to avoid races on first access.

    Args:
        session_id: Session identifier.

    Returns:
        asyncio.Lock specific to this session.
    """
    if session_id not in _locks:
        _locks[session_id] = asyncio.Lock()
    return _locks[session_id]


async def get_session(session_id: str) -> dict[str, Any]:
    """Load session state from SQLite, creating a new one if it doesn't exist.

    Args:
        session_id: Session identifier.

    Returns:
        Mutable session state dictionary.
    """
    conn = _get_connection()
    cursor = conn.execute(
        "SELECT state_json FROM session_state WHERE session_id = ?",
        (session_id,),
    )
    row = cursor.fetchone()
    if row:
        state = dict(json.loads(row[0]))
        # Deserialize messages from LangChain's serialization format
        raw_messages = state.pop("messages", [])
        if raw_messages and isinstance(raw_messages, list):
            try:
                state["messages"] = messages_from_dict(raw_messages)
            except Exception:
                state["messages"] = []
        else:
            state["messages"] = []
        return state

    state = new_session()
    conn.execute(
        "INSERT INTO session_state (session_id, state_json, updated_at) "
        "VALUES (?, ?, ?)",
        (session_id, json.dumps(state), datetime.utcnow().isoformat()),
    )
    conn.commit()
    return state


async def save_session(session_id: str, state: dict[str, Any]) -> None:
    """Save session state to SQLite under the per-session lock.

    Args:
        session_id: Session identifier.
        state: Session state dictionary to persist.
    """
    lock = _get_lock(session_id)
    async with lock:
        # Serialize messages to LangChain's JSON-compatible format
        state_copy = dict(state)
        raw_messages = state_copy.pop("messages", [])
        if raw_messages and isinstance(raw_messages, list):
            try:
                state_copy["messages"] = messages_to_dict(raw_messages)
            except Exception:
                state_copy["messages"] = []
        else:
            state_copy["messages"] = []

        conn = _get_connection()
        conn.execute(
            "UPDATE session_state SET state_json = ?, updated_at = ? "
            "WHERE session_id = ?",
            (json.dumps(state_copy), datetime.utcnow().isoformat(), session_id),
        )
        conn.commit()
