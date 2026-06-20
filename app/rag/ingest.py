"""
RAG Ingestion Pipeline
Loads PDF documents, chunks them, creates embeddings, and stores in ChromaDB
"""

import os

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.services.llm import get_embeddings
from config import APIConfig

load_dotenv()

# Use configuration from config.py
PDF_PATH = APIConfig.PDF_PATH
CHROMA_PERSIST_DIR = APIConfig.CHROMA_PERSIST_DIR


def ingest_documents():
    """
    Loads the PDF, chunks it, creates embeddings using HuggingFace, and stores in ChromaDB.
    This uses local embeddings (no API keys required).
    """
    print(f"Loading document from {PDF_PATH}...")
    loader = PyPDFLoader(PDF_PATH)
    documents = loader.load()
    print(f"Loaded {len(documents)} pages.")

    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.")

    print("Creating embeddings and storing in ChromaDB...")
    # Initialize HuggingFace Embeddings (local, no API keys needed)
    embeddings = get_embeddings()

    # Create Chroma vector store
    # This will create a new ChromaDB or load from existing if it finds one
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_DIR
    )
    print(f"Ingestion complete. {len(chunks)} chunks stored in ChromaDB at {CHROMA_PERSIST_DIR}")


if __name__ == "__main__":
    # Ensure the data/chroma_db directory exists
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    ingest_documents()


