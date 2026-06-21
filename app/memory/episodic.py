"""Episodic memory — per-user session summaries stored in Chroma.

The agent writes a short natural-language summary of each session (or every
N turns) to a dedicated Chroma collection.  When a new session starts, the
``load_memory`` graph node retrieves the top-k most relevant prior episodes
for the same ``user_id`` and injects them into ``AgentState.memory_hits``.

Architecture
------------
- Chroma collection ``episodic_memory``
- Metadata per chunk: ``{user_id, session_id, intent, created_at, summary}``
- Embeddings use the same ``get_embeddings()`` singleton as the RAG pipeline
  so the vector space is consistent.

Acceptance
----------
- New session for ``user_id=u1`` retrieves >= 1 prior episode within 50 ms
  (cold start aside; warm cache << 50 ms).
"""

import threading
from datetime import datetime
from typing import Any

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from app.services.llm import get_embeddings
from config import APIConfig

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EPISODIC_COLLECTION = "episodic_memory"

# ---------------------------------------------------------------------------
# Singleton state
# ---------------------------------------------------------------------------

_episodic_store: Chroma | None = None
_episodic_lock = threading.Lock()


def _get_store() -> Chroma:
    """Return a singleton Chroma instance pointed at the episodic collection."""
    global _episodic_store
    if _episodic_store is None:
        with _episodic_lock:
            if _episodic_store is None:
                embeddings = get_embeddings()
                _episodic_store = Chroma(
                    persist_directory=APIConfig.CHROMA_PERSIST_DIR,
                    embedding_function=embeddings,
                    collection_name=EPISODIC_COLLECTION,
                )
    return _episodic_store


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class EpisodicMemory:
    """Per-user episodic (session-summary) memory backed by Chroma."""

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @staticmethod
    def store_episode(
        user_id: str,
        session_id: str,
        summary: str,
        intent: str = "",
    ) -> None:
        """Write a session summary to the episodic memory store.

        Parameters
        ----------
        user_id:
            The user this episode belongs to.
        session_id:
            The session that generated this episode.
        summary:
            Natural-language summary of what happened in the session, e.g.
            *"User asked about order #1234, learned it was delayed, requested a
             callback. Outcome: callback scheduled."*
        intent:
            Optional high-level intent label (``order_status``, ``return``, …).
        """
        store = _get_store()
        doc = Document(
            page_content=summary,
            metadata={
                "user_id": user_id,
                "session_id": session_id,
                "intent": intent,
                "created_at": datetime.utcnow().isoformat(),
                "summary": summary,
            },
        )
        store.add_documents([doc])

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @staticmethod
    def retrieve_episodes(
        user_id: str,
        query: str = "",
        k: int = 3,
    ) -> list[dict[str, Any]]:
        """Retrieve the most relevant prior episodes for *user_id*.

        Parameters
        ----------
        user_id:
            Only episodes belonging to this user are returned.
        query:
            Current user query — used for semantic similarity. If empty,
            falls back to most recent.
        k:
            Max number of episodes to return.

        Returns
        -------
        List of dicts with keys ``summary``, ``session_id``, ``intent``,
        ``created_at``, ``score``.
        """
        store = _get_store()

        if query:
            results = store.similarity_search_with_score(
                query,
                k=k * 3,  # over-fetch so we can filter
                filter={"user_id": user_id},
            )
        else:
            results = store.similarity_search_with_score(
                user_id,
                k=k * 3,
                filter={"user_id": user_id},
            )

        episodes: list[dict[str, Any]] = []
        seen: set[str] = set()
        for doc, score in results:
            meta = doc.metadata
            sid = meta.get("session_id", "")
            if sid in seen:
                continue
            seen.add(sid)
            episodes.append(
                {
                    "summary": doc.page_content,
                    "session_id": sid,
                    "intent": meta.get("intent", ""),
                    "created_at": meta.get("created_at", ""),
                    "score": float(score),
                }
            )
            if len(episodes) >= k:
                break

        return episodes

    # ------------------------------------------------------------------
    # Build a summary from conversation messages
    # ------------------------------------------------------------------

    @staticmethod
    def build_and_store_summary(
        user_id: str,
        session_id: str,
        messages: list,
        intent: str = "",
    ) -> None:
        """Build a concise summary from the last few messages and store it.

        Uses a heuristic: extracts the first user message (the goal) and
        the last assistant message (the outcome) to form a summary.

        For v1, this is a simple heuristic.  In v2 this should use the LLM
        to generate a proper summary.
        """
        # Extract key messages
        user_goals: list[str] = []
        assistant_replies: list[str] = []
        for msg in messages:
            role = getattr(msg, "type", "")
            content = getattr(msg, "content", "")
            if isinstance(content, list):
                content = " ".join(
                    c.get("text", "") if isinstance(c, dict) else str(c)
                    for c in content
                )
            if role == "human":
                user_goals.append(str(content)[:200])
            elif role == "ai":
                assistant_replies.append(str(content)[:200])

        # Build a compact summary
        first_goal = user_goals[0] if user_goals else "Unknown"
        last_outcome = assistant_replies[-1] if assistant_replies else ""
        summary = (
            f"User asked: {first_goal[:150]}. "
            f"{'Outcome: ' + last_outcome[:150] + '.' if last_outcome else 'Session in progress.'}"
        )

        EpisodicMemory.store_episode(
            user_id=user_id,
            session_id=session_id,
            summary=summary,
            intent=intent,
        )

    # ------------------------------------------------------------------
    # Count
    # ------------------------------------------------------------------

    @staticmethod
    def count() -> int:
        """Return the number of stored episodes (for diagnostics)."""
        store = _get_store()
        return store._collection.count()  # type: ignore[attr-defined]
