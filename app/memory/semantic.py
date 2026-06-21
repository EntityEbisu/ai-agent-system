"""Semantic memory — key-value user facts stored in SQLite.

The agent learns facts about each user over time (preferred shipping address,
whether they are a VIP customer, last complaint topic, etc.) and can recall
them on demand via ``record_fact`` / ``recall_facts`` tools.

Schema
------
.. code-block:: sql

    CREATE TABLE user_facts (
        user_id         TEXT NOT NULL,
        key             TEXT NOT NULL,
        value           TEXT NOT NULL,
        source_session  TEXT,
        confidence      REAL DEFAULT 1.0,
        updated_at      TEXT NOT NULL,
        PRIMARY KEY (user_id, key)
    )

Notes
-----
- Keys are free-form strings.  Keep them simple and consistent
  (``preferred_shipping_address``, ``is_vip``, …).
- Confidence is 0.0–1.0.  The agent should only store facts it is confident
  about (confidence >= 0.8).
- A future admin tool ``migrate_user_facts(key_v1, key_v2)`` will handle
  schema evolution (v2-track).
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path / connection helpers
# ---------------------------------------------------------------------------

_FACTS_DB: Path = Path("data/sqlite/user_facts.db")


def _get_conn() -> sqlite3.Connection:
    _FACTS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_FACTS_DB))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_facts (
            user_id        TEXT NOT NULL,
            key            TEXT NOT NULL,
            value          TEXT NOT NULL,
            source_session TEXT,
            confidence     REAL DEFAULT 1.0,
            updated_at     TEXT NOT NULL,
            PRIMARY KEY (user_id, key)
        )
        """
    )
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class SemanticMemory:
    """Key-value user facts backed by SQLite.

    Usage::

        SemanticMemory.record_fact("u1", "preferred_shipping_address",
                                    "123 Main St", session_id="sess_1")
        facts = SemanticMemory.recall_facts("u1", key_prefix="preferred")
    """

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @staticmethod
    def record_fact(
        user_id: str,
        key: str,
        value: str,
        source_session: str | None = None,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """Store or update a fact about *user_id*.

        Parameters
        ----------
        user_id:
            The user this fact belongs to.
        key:
            Fact name (e.g. ``preferred_shipping_address``).
        value:
            Fact value (e.g. ``"123 Main St"``).
        source_session:
            Session identifier where this fact was learned.
        confidence:
            0.0–1.0.  Consider skipping facts with confidence < 0.6.

        Returns
        -------
        ``{"status": "saved", "user_id": …, "key": …}``
        """
        conn = _get_conn()
        now = datetime.utcnow().isoformat()
        conn.execute(
            """
            INSERT INTO user_facts (user_id, key, value, source_session, confidence, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, key) DO UPDATE SET
                value          = excluded.value,
                source_session = excluded.source_session,
                confidence     = excluded.confidence,
                updated_at     = excluded.updated_at
            """,
            (user_id, key, value, source_session, min(max(confidence, 0.0), 1.0), now),
        )
        conn.commit()
        return {"status": "saved", "user_id": user_id, "key": key}

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @staticmethod
    def recall_facts(
        user_id: str,
        key_prefix: str = "",
    ) -> list[dict[str, Any]]:
        """Return all facts for *user_id*, optionally filtered by *key_prefix*.

        Returns
        -------
        List of dicts with keys ``key``, ``value``, ``confidence``,
        ``source_session``, ``updated_at``, sorted by ``updated_at`` desc.
        """
        conn = _get_conn()
        if key_prefix:
            rows = conn.execute(
                """
                SELECT key, value, confidence, source_session, updated_at
                FROM user_facts
                WHERE user_id = ? AND key LIKE ?
                ORDER BY updated_at DESC
                """,
                (user_id, f"{key_prefix}%"),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT key, value, confidence, source_session, updated_at
                FROM user_facts
                WHERE user_id = ?
                ORDER BY updated_at DESC
                """,
                (user_id,),
            ).fetchall()

        return [
            {
                "key": r[0],
                "value": r[1],
                "confidence": r[2],
                "source_session": r[3],
                "updated_at": r[4],
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @staticmethod
    def delete_fact(user_id: str, key: str) -> dict[str, Any]:
        """Remove a single fact for *user_id*.

        Returns
        -------
        ``{"status": "deleted", "user_id": …, "key": …}``
        or ``{"status": "not_found"}``
        """
        conn = _get_conn()
        cur = conn.execute(
            "DELETE FROM user_facts WHERE user_id = ? AND key = ?",
            (user_id, key),
        )
        conn.commit()
        if cur.rowcount == 0:
            return {"status": "not_found"}
        return {"status": "deleted", "user_id": user_id, "key": key}

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    @staticmethod
    def count(user_id: str = "") -> int:
        """Count facts, optionally for a single user."""
        conn = _get_conn()
        if user_id:
            row = conn.execute(
                "SELECT COUNT(*) FROM user_facts WHERE user_id = ?", (user_id,)
            ).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) FROM user_facts").fetchone()
        return row[0] if row else 0
