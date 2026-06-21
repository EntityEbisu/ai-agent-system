"""
RAG Data Lifecycle Management
Handles document versioning, updates, and metadata tracking for FAQ/policy updates.
Supports incremental updates to knowledge base without full re-ingestion.
"""

import hashlib
import json
import os
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma

import config
from app.rag.chunker import get_semantic_chunker
from app.services.llm import get_embeddings


@dataclass
class DocumentMetadata:
    """Metadata for tracked documents."""
    document_id: str
    filename: str
    version: int
    content_hash: str
    ingested_at: str
    updated_at: str
    chunks_count: int
    source_path: str
    description: str = ""
    tags: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_instance = None
_instance_lock = threading.Lock()


class RAGDataLifecycle:
    """Manages document versioning and lifecycle in Chroma.

    Singleton — call ``RAGDataLifecycle.get_instance()`` to reuse the
    same embedding model across requests instead of loading it per-call.
    """

    @classmethod
    def get_instance(cls) -> "RAGDataLifecycle":
        """Return the shared singleton, creating it on first call."""
        global _instance
        if _instance is None:
            with _instance_lock:
                if _instance is None:
                    _instance = cls()
        return _instance

    def __init__(self, chroma_persist_dir: str = config.APIConfig.CHROMA_PERSIST_DIR):
        self.chroma_persist_dir = chroma_persist_dir
        self.metadata_file = Path(chroma_persist_dir) / "document_metadata.json"
        self.embeddings = get_embeddings()
        self.db = None
        self._collection = None
        self._collection_lock = threading.Lock()
        self._metadata_lock = threading.Lock()
        self._load_metadata()

    def _get_collection(self):
        """Lazy-init the Chroma collection handle for delete operations."""
        if self._collection is None:
            with self._collection_lock:
                if self._collection is None:
                    from langchain_community.vectorstores import Chroma
                    chroma = Chroma(
                        persist_directory=self.chroma_persist_dir,
                        embedding_function=self.embeddings,
                        collection_name=config.APIConfig.CHROMA_COLLECTION,
                    )
                    self._collection = chroma._collection
        return self._collection

    def _load_metadata(self) -> dict[str, dict[str, Any]]:
        """Load document metadata from file."""
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                return json.load(f)
        return {}

    def _save_metadata(self, metadata: dict[str, dict[str, Any]]):
        """Save document metadata to file atomically.

        Writes to a ``.tmp`` file then renames (``os.replace``), so a crash
        mid-write never corrupts the persistent file.  Thread-safe via a
        per-instance lock.
        """
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.metadata_file.with_suffix(".json.tmp")
        with self._metadata_lock:
            with open(tmp, 'w') as f:
                json.dump(metadata, f, indent=2)
            os.replace(tmp, self.metadata_file)

    @staticmethod
    def _compute_hash(content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def ingest_document(self, file_path: str, description: str = "", tags: list[str] | None = None) -> dict[str, Any]:
        """
        Ingest a new document or update existing one.

        Returns metadata about ingestion including version and chunk count.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        # Load document
        if file_path.suffix.lower() == '.pdf':
            loader = PyPDFLoader(str(file_path))
            documents = loader.load()
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        # Combine content for hashing
        full_content = "\n".join([doc.page_content for doc in documents])
        content_hash = self._compute_hash(full_content)

        # Load existing metadata
        metadata = self._load_metadata()
        doc_id = file_path.stem

        # Check if document exists and if it has changed
        existing_version = 1
        if doc_id in metadata:
            existing = metadata[doc_id]
            if existing.get("content_hash") == content_hash:
                # No change, return existing metadata
                return {
                    "status": "unchanged",
                    "document_id": doc_id,
                    "message": "Document content unchanged, no update needed",
                    "metadata": existing
                }
            existing_version = existing.get("version", 1) + 1

        # Split into chunks using semantic chunking
        text_splitter = get_semantic_chunker()
        chunks = text_splitter.split_documents(documents)

        # Tag each chunk with the document_id for lifecycle management
        for chunk in chunks:
            chunk.metadata["document_id"] = doc_id

        # Store in Chroma with metadata
        Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.chroma_persist_dir,
            collection_name=config.APIConfig.CHROMA_COLLECTION
        )

        # Update metadata
        doc_metadata = DocumentMetadata(
            document_id=doc_id,
            filename=file_path.name,
            version=existing_version,
            content_hash=content_hash,
            ingested_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            chunks_count=len(chunks),
            source_path=str(file_path),
            description=description,
            tags=tags or []
        )

        metadata[doc_id] = doc_metadata.to_dict()
        self._save_metadata(metadata)

        return {
            "status": "success",
            "document_id": doc_id,
            "version": existing_version,
            "chunks_count": len(chunks),
            "content_hash": content_hash,
            "message": f"Document ingested successfully (v{existing_version}, {len(chunks)} chunks)",
            "metadata": doc_metadata.to_dict()
        }

    def list_document_versions(self) -> list[dict[str, Any]]:
        """List all tracked documents with version history."""
        metadata = self._load_metadata()
        return [
            {
                "document_id": doc_id,
                "filename": info.get("filename"),
                "version": info.get("version"),
                "ingested_at": info.get("ingested_at"),
                "updated_at": info.get("updated_at"),
                "chunks_count": info.get("chunks_count"),
                "tags": info.get("tags", [])
            }
            for doc_id, info in metadata.items()
        ]

    def get_document_metadata(self, document_id: str) -> dict[str, Any] | None:
        """Get metadata for a specific document."""
        metadata = self._load_metadata()
        return metadata.get(document_id)

    def archive_document(self, document_id: str) -> dict[str, Any]:
        """Archive a document — removes vectors from Chroma, keeps metadata.

        The document's vectors are deleted from Chroma so they no longer
        appear in retrieval results.  The JSON metadata is preserved for
        audit purposes.
        """
        metadata = self._load_metadata()

        if document_id not in metadata:
            return {"status": "error", "message": f"Document '{document_id}' not found"}

        # Remove vectors from Chroma
        try:
            collection = self._get_collection()
            collection.delete(where={"document_id": document_id})
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to delete vectors for '{document_id}': {e}",
            }

        # Keep metadata for audit trail
        metadata[document_id]["archived_at"] = datetime.utcnow().isoformat()
        metadata[document_id]["active"] = False
        self._save_metadata(metadata)

        return {
            "status": "success",
            "document_id": document_id,
            "message": f"Document '{document_id}' archived ({metadata[document_id].get('chunks_count', 0)} vectors removed)",
        }

    def restore_document(self, document_id: str) -> dict[str, Any]:
        """Restore an archived document."""
        metadata = self._load_metadata()

        if document_id not in metadata:
            return {"status": "error", "message": f"Document '{document_id}' not found"}

        metadata[document_id]["active"] = True
        metadata[document_id].pop("archived_at", None)
        self._save_metadata(metadata)

        return {
            "status": "success",
            "document_id": document_id,
            "message": f"Document '{document_id}' restored"
        }

    def get_ingestion_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get ingestion history ordered by date."""
        metadata = self._load_metadata()

        history = []
        for doc_id, info in metadata.items():
            history.append({
                "document_id": doc_id,
                "filename": info.get("filename"),
                "version": info.get("version"),
                "updated_at": info.get("updated_at"),
                "chunks_count": info.get("chunks_count"),
                "active": info.get("active", True)
            })

        # Sort by update time, newest first
        history.sort(
            key=lambda x: x.get("updated_at", ""),
            reverse=True
        )

        return history[:limit]

    def get_lifecycle_stats(self) -> dict[str, Any]:
        """Get statistics about document lifecycle."""
        metadata = self._load_metadata()

        active_docs = [m for m in metadata.values() if m.get("active", True)]
        archived_docs = [m for m in metadata.values() if not m.get("active", True)]

        total_chunks = sum(m.get("chunks_count", 0) for m in active_docs)

        return {
            "total_documents": len(metadata),
            "active_documents": len(active_docs),
            "archived_documents": len(archived_docs),
            "total_chunks": total_chunks,
            "latest_update": max(
                [m.get("updated_at", "") for m in metadata.values()],
                default=None
            )
        }


class DocumentUpdateTracker:
    """Tracks changes and updates to documents for audit and versioning."""

    def __init__(self, tracking_file: str = "data/document_updates.json"):
        self.tracking_file = Path(tracking_file)
        self._ensure_file()

    def _ensure_file(self):
        """Ensure tracking file exists."""
        self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.tracking_file.exists():
            with open(self.tracking_file, 'w') as f:
                json.dump([], f)

    def record_update(self, document_id: str, change_type: str,
                     old_version: int, new_version: int,
                     change_summary: str = "") -> dict[str, Any]:
        """Record a document update."""
        with open(self.tracking_file) as f:
            updates = json.load(f)

        update_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "document_id": document_id,
            "change_type": change_type,  # "ingested", "updated", "archived", "restored"
            "old_version": old_version,
            "new_version": new_version,
            "summary": change_summary
        }

        updates.append(update_record)

        with open(self.tracking_file, 'w') as f:
            json.dump(updates, f, indent=2)

        return update_record

    def get_update_history(self, document_id: str | None = None) -> list[dict[str, Any]]:
        """Get update history for a document or all documents."""
        with open(self.tracking_file) as f:
            updates = json.load(f)

        if document_id:
            updates = [u for u in updates if u.get("document_id") == document_id]

        return sorted(updates, key=lambda x: x.get("timestamp", ""), reverse=True)
