from collections.abc import AsyncGenerator

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.rag.retriever import get_retriever  # Import get_retriever from its new location
from app.services.llm import get_llm


def handle_rag(query: str, state: dict) -> str:
    """
    Synchronous RAG handler (for cases where streaming is not needed or as a fallback).
    """
    llm = get_llm()
    retriever = get_retriever()

    # Retrieve documents
    docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in docs])

    # Create prompt with context
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
    response = chain.invoke({"context": context, "question": query})

    return response

async def handle_rag_stream(query: str, state: dict) -> AsyncGenerator[str, None]:
    """Async RAG handler with streaming response."""
    llm = get_llm(streaming=True)
    retriever = get_retriever()

    # Retrieve documents
    docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in docs])

    # Create prompt with context
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

    # Stream the response using astream
    async for chunk in chain.astream({"context": context, "question": query}):
        yield chunk

def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])

