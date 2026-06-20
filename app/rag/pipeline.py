"""RAG pipeline — retrieval-augmented generation with streaming support.

The sync ``handle_rag`` wraps its blocking LLM call in ``asyncio.to_thread``
so it does not stall the event loop when called from async code.
"""

import asyncio
from collections.abc import AsyncGenerator

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.rag.retriever import get_retriever
from app.services.llm import get_llm


async def handle_rag(query: str, state: dict) -> str:
    """Async RAG handler — runs the blocking LLM call in a thread.

    Args:
        query: User question.
        state: Conversation state dictionary.

    Returns:
        Generated response text.
    """
    llm = get_llm()
    retriever = get_retriever()

    # Retrieve documents (runs in thread to avoid blocking)
    docs = await asyncio.to_thread(retriever.invoke, query)
    context = "\n\n".join([doc.page_content for doc in docs])

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an AI assistant for an e-commerce company. "
            "Answer the user's question based on the provided documents. "
            "If the answer is not in the documents, state that you don't know. "
            "Do not make up answers.\n\nContext:\n{context}"
        )),
        ("user", "{question}")
    ])

    chain = prompt_template | llm | StrOutputParser()

    # Run blocking chain.invoke in a thread
    response = await asyncio.to_thread(
        chain.invoke, {"context": context, "question": query}
    )
    return response


async def handle_rag_stream(query: str, state: dict) -> AsyncGenerator[str, None]:
    """Async RAG handler with streaming response.

    Args:
        query: User question.
        state: Conversation state dictionary.

    Yields:
        Response text chunks as they are generated.
    """
    llm = get_llm(streaming=True)
    retriever = get_retriever()

    # Retrieve documents (runs in thread to avoid blocking)
    docs = await asyncio.to_thread(retriever.invoke, query)
    context = "\n\n".join([doc.page_content for doc in docs])

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an AI assistant for an e-commerce company. "
            "Answer the user's question based on the provided documents. "
            "If the answer is not in the documents, state that you don't know. "
            "Do not make up answers.\n\nContext:\n{context}"
        )),
        ("user", "{question}")
    ])

    chain = prompt_template | llm | StrOutputParser()

    # astream is already async — no to_thread needed
    async for chunk in chain.astream({"context": context, "question": query}):
        yield chunk


def format_docs(docs):
    """Format retrieved documents into a single context string.

    Args:
        docs: List of LangChain Document objects.

    Returns:
        Concatenated text with double-newline separators.
    """
    return "\n\n".join([doc.page_content for doc in docs])
