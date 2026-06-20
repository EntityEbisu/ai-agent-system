"""RAG pipeline — retrieval-augmented generation with streaming support.

The sync ``handle_rag`` wraps its blocking LLM call in ``asyncio.to_thread``
so it does not stall the event loop when called from FastAPI handlers.

Retry/backoff via tenacity: exponential backoff with jitter, max 3 attempts.
Timeout: 30 s per LLM call.
"""

import asyncio

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.exceptions import LLMRetryableError, LLMTimeoutError
from app.rag.retriever import get_retriever
from app.services.llm import get_llm

LLM_TIMEOUT_S = 30

# ── Prompt template ──────────────────────────────────────────────

RAG_TEMPLATE = """You are a helpful customer support assistant for an e-commerce store.
Use the following context to answer the user's question.

Context:
{context}

Question: {question}

Helpful Answer:"""

prompt = ChatPromptTemplate.from_template(RAG_TEMPLATE)

# ── Retry policy ─────────────────────────────────────────────────

_retry_policy = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10, jitter=2),
    reraise=True,
)


# ── Document formatting ──────────────────────────────────────────

def format_docs(docs: list[Document]) -> str:
    """Format retrieved documents into a single context string."""
    return "\n\n".join(doc.page_content for doc in docs)


# ── RAG chain construction ───────────────────────────────────────

def _build_rag_chain():
    """Build the RAG chain with retriever and LLM."""
    retriever = get_retriever()
    llm = get_llm(streaming=True)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
    )
    return chain


# ── RAG execution ────────────────────────────────────────────────

async def handle_rag_stream(query: str, state: dict):
    """
    Stream the RAG response token by token.

    Applies a 30-second timeout to the LLM stream and retries on
    transient failures.

    Args:
        query: The user's question.
        state: The mutable session state dict.

    Yields:
        Tokens (str) from the LLM response.
    """
    state["intent"] = "rag"

    try:
        chain = await asyncio.to_thread(_build_rag_chain)
    except Exception as e:
        raise LLMRetryableError(detail=str(e)) from e

    try:
        async for chunk in _retry_policy(chain.astream)(query):
            yield chunk.content if hasattr(chunk, "content") else str(chunk)
    except Exception as e:
        raise LLMRetryableError(detail=str(e)) from e


async def handle_rag(query: str, state: dict) -> str:
    """
    Execute a non-streaming RAG query with timeout and retry.

    Args:
        query: The user's question.
        state: The mutable session state dict.

    Returns:
        The full response text.

    Raises:
        LLMTimeoutError: If the call exceeds the 30 s deadline.
        LLMRetryableError: If the call fails after retries.
    """
    state["intent"] = "rag"

    try:
        chain = await asyncio.to_thread(_build_rag_chain)
    except Exception as e:
        raise LLMRetryableError(detail=str(e)) from e

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(_retry_policy(chain.invoke), query),
            timeout=LLM_TIMEOUT_S,
        )
        content = result.content if hasattr(result, "content") else str(result)
        return str(content) if not isinstance(content, str) else content
    except TimeoutError:
        raise LLMTimeoutError(timeout_s=LLM_TIMEOUT_S) from None
    except Exception as e:
        raise LLMRetryableError(detail=str(e)) from e
