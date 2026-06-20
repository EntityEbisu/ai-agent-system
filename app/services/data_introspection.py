"""
Data Introspection Tools
Provides visibility into SQLite, Chroma, and system metrics.
Supports querying session data, message history, document chunks, and metrics.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any

from app.rag.retriever import get_retriever


class DatabaseIntrospection:
    """Tools for inspecting SQLite conversation database."""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.db_path = db_url.replace("sqlite:///", "")

    def get_session_summary(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get summary of recent sessions."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
        SELECT id, created_at, ended_at, context_type, messages_count
        FROM conversation_sessions
        ORDER BY created_at DESC
        LIMIT ?
        """
        cursor.execute(query, (limit,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_session_messages(self, session_id: str) -> list[dict[str, Any]]:
        """Get all messages in a session with metadata."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
        SELECT id, role, content, created_at, tokens_used, processing_time_ms, intent
        FROM messages
        WHERE session_id = ?
        ORDER BY created_at ASC
        """
        cursor.execute(query, (session_id,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_metrics_snapshot(self) -> dict[str, Any]:
        """Get current metrics snapshot."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        stats = {
            "total_sessions": 0,
            "total_messages": 0,
            "total_tool_executions": 0,
            "avg_tokens_per_message": 0,
            "avg_latency_ms": 0,
            "latest_activity": None
        }

        # Total sessions
        cursor.execute("SELECT COUNT(*) as count FROM conversation_sessions")
        stats["total_sessions"] = cursor.fetchone()["count"]

        # Total messages
        cursor.execute("SELECT COUNT(*) as count FROM messages")
        stats["total_messages"] = cursor.fetchone()["count"]

        # Total tool executions
        cursor.execute("SELECT COUNT(*) as count FROM tool_executions")
        stats["total_tool_executions"] = cursor.fetchone()["count"]

        # Average tokens per message
        cursor.execute("""
        SELECT AVG(tokens_used) as avg_tokens
        FROM messages
        WHERE tokens_used IS NOT NULL
        """)
        result = cursor.fetchone()
        if result["avg_tokens"]:
            stats["avg_tokens_per_message"] = round(result["avg_tokens"], 2)

        # Average latency
        cursor.execute("""
        SELECT AVG(processing_time_ms) as avg_latency
        FROM messages
        WHERE processing_time_ms IS NOT NULL
        """)
        result = cursor.fetchone()
        if result["avg_latency"]:
            stats["avg_latency_ms"] = round(result["avg_latency"], 2)

        # Latest activity
        cursor.execute("""
        SELECT created_at FROM messages
        ORDER BY created_at DESC
        LIMIT 1
        """)
        result = cursor.fetchone()
        if result:
            stats["latest_activity"] = result["created_at"]

        conn.close()
        return stats

    def get_token_usage_report(self, hours: int = 24) -> dict[str, Any]:
        """Get token usage report for the last N hours."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        query = """\
        SELECT
            COUNT(*) as message_count,
            SUM(tokens_used) as total_tokens,
            AVG(tokens_used) as avg_tokens,
            MIN(tokens_used) as min_tokens,
            MAX(tokens_used) as max_tokens
        FROM messages
        WHERE created_at > ? AND tokens_used IS NOT NULL
        """
        cursor.execute(query, (cutoff_time.isoformat(),))
        result = dict(cursor.fetchone())
        conn.close()

        return {
            "time_period_hours": hours,
            "cutoff_time": cutoff_time.isoformat(),
            **result
        }

    def get_latency_report(self, hours: int = 24) -> dict[str, Any]:
        """Get latency statistics for the last N hours."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        query = """\
        SELECT
            COUNT(*) as request_count,
            AVG(processing_time_ms) as avg_latency,
            MIN(processing_time_ms) as min_latency,
            MAX(processing_time_ms) as max_latency,
            COUNT(CASE WHEN processing_time_ms > 1000 THEN 1 END) as slow_requests
        FROM messages
        WHERE created_at > ? AND processing_time_ms IS NOT NULL
        """
        cursor.execute(query, (cutoff_time.isoformat(),))
        result = dict(cursor.fetchone())
        conn.close()

        return {
            "time_period_hours": hours,
            "cutoff_time": cutoff_time.isoformat(),
            **{k: round(v, 2) if isinstance(v, float) else v for k, v in result.items()}
        }

    def export_session_as_json(self, session_id: str) -> str:
        """Export a complete session as JSON."""
        messages = self.get_session_messages(session_id)
        return json.dumps({
            "session_id": session_id,
            "message_count": len(messages),
            "messages": messages
        }, indent=2, default=str)


class ChromaIntrospection:
    """Tools for inspecting Chroma vector database."""

    def __init__(self):
        self.retriever = get_retriever()

    def list_documents(self, limit: int = 50) -> list[dict[str, Any]]:
        """List ingested documents with metadata."""
        try:
            # This is a simplified version - full implementation depends on Chroma API
            chroma_client = self.retriever._collection

            results = []
            # Get collection info
            count = chroma_client.count()

            # Get sample documents (Chroma doesn't have direct list API)
            all_docs = chroma_client.get(
                limit=limit,
                include=["documents", "metadatas", "distances"]
            )

            for i, (doc, meta) in enumerate(zip(
                all_docs.get("documents", []),
                all_docs.get("metadatas", []), strict=False
            )):
                results.append({
                    "id": all_docs.get("ids", [])[i] if i < len(all_docs.get("ids", [])) else f"doc_{i}",
                    "content_preview": doc[:100] if isinstance(doc, str) else str(doc)[:100],
                    "content_length": len(doc) if isinstance(doc, str) else len(str(doc)),
                    "metadata": meta
                })

            return {
                "total_documents": count,
                "returned": len(results),
                "documents": results
            }  # type: ignore[return-value]
        except Exception as e:
            return {"error": str(e), "message": "Could not retrieve document list"}  # type: ignore[return-value]

    def test_retrieval(self, query: str, k: int = 5) -> dict[str, Any]:
        """Test retrieval for a query and return results."""
        try:
            docs = self.retriever.invoke(query)

            return {
                "query": query,
                "k_requested": k,
                "results_returned": len(docs),
                "documents": [
                    {
                        "content": doc.page_content[:200],
                        "content_length": len(doc.page_content),
                        "metadata": doc.metadata if hasattr(doc, "metadata") else {}
                    }
                    for doc in docs
                ]
            }
        except Exception as e:
            return {"error": str(e), "query": query}


class MetricsIntrospection:
    """Tools for inspecting system metrics."""

    @staticmethod
    def get_formatted_metrics_report() -> str:
        """Get a formatted report of system metrics."""
        from app.main import get_metrics_instance

        metrics = get_metrics_instance()
        summary = metrics.get_summary()

        report = "=== System Metrics Report ===\n\n"

        for endpoint, data in summary.items():
            if isinstance(data, dict):
                report += f"{endpoint}:\n"
                for key, value in data.items():
                    if isinstance(value, float):
                        report += f"  {key}: {value:.2f}\n"
                    else:
                        report += f"  {key}: {value}\n"
                report += "\n"

        return report
