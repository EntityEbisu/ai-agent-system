"""Validation helper for the current project.

Run this script from the repository root with the virtual environment active:

    python tests/validate_project.py

It verifies:
- Chroma retrieval from the local vector store
- Order status workflow slot collection and completion
- Optional RAG chain behavior if OpenRouter is configured
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.agent.router import handle_message
from app.agent.memory import get_session
from app.services.llm import get_embeddings
from app.rag.retriever import get_retriever
from config import APIConfig
from langchain_community.vectorstores import Chroma


def test_chroma():
    print("=== Chroma Validation ===")
    embeddings = get_embeddings()
    db = Chroma(
        persist_directory=APIConfig.CHROMA_PERSIST_DIR,
        embedding_function=embeddings,
    )
    docs = db.similarity_search("seasonality", k=2)
    print(f"Retrieved {len(docs)} document chunk(s).")
    for i, doc in enumerate(docs, start=1):
        print(f"--- chunk {i} ---")
        print(doc.page_content[:400].replace("\n", " "))
    print("=== Chroma Validation Complete ===\n")


def test_workflow():
    print("=== Order Workflow Validation ===")
    state = get_session("validate-workflow")

    prompts = [
        "I want to check my order status.",
        "Alice Nguyen",
        "1234",
        "1990-01-01",
    ]

    for prompt in prompts:
        response = handle_message(prompt, state)
        print(f"User: {prompt}")
        print(f"Assistant: {response}\n")

    print("Final tool state:", state["tool_state"])
    print("=== Order Workflow Validation Complete ===\n")


async def test_rag_stream():
    print("=== Optional RAG Stream Validation ===")
    try:
        retriever = get_retriever()
        docs = retriever.invoke("What are the main risks for international operations?")
        print(f"Retrieved {len(docs)} docs from retriever.")
        if docs:
            print(f"First doc preview: {docs[0].page_content[:300]}")
    except Exception as exc:
        print("RAG retriever check failed:", exc)
        import traceback
        traceback.print_exc()
        return

    print("=== Optional RAG Stream Validation Complete ===\n")


def main():
    test_chroma()
    test_workflow()
    asyncio.run(test_rag_stream())


if __name__ == "__main__":
    main()
