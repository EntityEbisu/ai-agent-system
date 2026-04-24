"""
RAG Data Lifecycle Management
Handles document versioning, updates, and metadata tracking for FAQ/policy updates.
Supports incremental updates to knowledge base without full re-ingestion.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
from dataclasses import dataclass, asdict

from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.llm import get_embeddings
import config

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
    tags: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RAGDataLifecycle:
    """Manages document versioning and lifecycle in Chroma."""
    
    def __init__(self, chroma_persist_dir: str = config.APIConfig.CHROMA_PERSIST_DIR):
        self.chroma_persist_dir = chroma_persist_dir
        self.metadata_file = Path(chroma_persist_dir) / "document_metadata.json"
        self.embeddings = get_embeddings()
        self.db = None
        self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load document metadata from file."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self, metadata: Dict[str, Dict[str, Any]]):
        """Save document metadata to file."""
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    @staticmethod
    def _compute_hash(content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def ingest_document(self, file_path: str, description: str = "", tags: List[str] = None) -> Dict[str, Any]:
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
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            add_start_index=True,
        )
        chunks = text_splitter.split_documents(documents)
        
        # Store in Chroma with metadata
        db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.chroma_persist_dir,
            collection_name="documents"
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
    
    def list_document_versions(self) -> List[Dict[str, Any]]:
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
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific document."""
        metadata = self._load_metadata()
        return metadata.get(document_id)
    
    def archive_document(self, document_id: str) -> Dict[str, Any]:
        """Mark a document as archived (soft delete)."""
        metadata = self._load_metadata()
        
        if document_id not in metadata:
            return {"status": "error", "message": f"Document '{document_id}' not found"}
        
        metadata[document_id]["archived_at"] = datetime.utcnow().isoformat()
        metadata[document_id]["active"] = False
        self._save_metadata(metadata)
        
        return {
            "status": "success",
            "document_id": document_id,
            "message": f"Document '{document_id}' archived"
        }
    
    def restore_document(self, document_id: str) -> Dict[str, Any]:
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
    
    def get_ingestion_history(self, limit: int = 50) -> List[Dict[str, Any]]:
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
    
    def get_lifecycle_stats(self) -> Dict[str, Any]:
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
                     change_summary: str = "") -> Dict[str, Any]:
        """Record a document update."""
        with open(self.tracking_file, 'r') as f:
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
    
    def get_update_history(self, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get update history for a document or all documents."""
        with open(self.tracking_file, 'r') as f:
            updates = json.load(f)
        
        if document_id:
            updates = [u for u in updates if u.get("document_id") == document_id]
        
        return sorted(updates, key=lambda x: x.get("timestamp", ""), reverse=True)
