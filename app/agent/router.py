"""Message router — classifies intent and dispatches to the right handler.

Routing decisions:
- If a tool workflow is active, continue it.
- Otherwise classify the message as ``order_status`` or ``rag``.
- ``rag`` intents use the streaming RAG pipeline.
"""

from collections.abc import AsyncGenerator

from app.rag.pipeline import handle_rag, handle_rag_stream

from .workflow import handle_tool_flow, start_tool_flow


async def handle_message(query: str, state: dict) -> str:
    """Synchronous-style message handler (internally async).

    Args:
        query: User message text.
        state: Conversation state dictionary (mutated in-place).

    Returns:
        Response text.
    """
    if state["tool_state"]["active"]:
        return handle_tool_flow(query, state)

    intent = classify(query)
    state["intent"] = intent

    if intent == "order_status":
        return start_tool_flow(state)

    return await handle_rag(query, state)


async def handle_message_stream(query: str, state: dict) -> AsyncGenerator[str, None]:
    """Streaming message handler — yields response chunks.

    Args:
        query: User message text.
        state: Conversation state dictionary (mutated in-place).

    Yields:
        Response text chunks.
    """
    # 1. Continue tool workflow if active
    if state["tool_state"]["active"]:
        yield handle_tool_flow(query, state)
        return

    # 2. Classify intent
    intent = classify(query)
    state["intent"] = intent

    # 3. Route
    if intent == "order_status":
        yield start_tool_flow(state)
        return

    # 4. RAG with streaming
    async for chunk in handle_rag_stream(query, state):
        yield chunk


def classify(query: str) -> str:
    """Classify a user query into an intent category.

    Args:
        query: The user's input message.

    Returns:
        One of ``"order_status"`` or ``"rag"``.
    """
    query = query.lower()

    if any(k in query for k in ["order", "track", "package", "where is my"]):
        return "order_status"

    return "rag"
