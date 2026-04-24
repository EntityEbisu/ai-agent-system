from .workflow import handle_tool_flow, start_tool_flow
from app.rag.pipeline import handle_rag, handle_rag_stream
from typing import AsyncGenerator

def handle_message(query: str, state: dict) -> str:
    # Synchronous version (fallback/internal)
    if state["tool_state"]["active"]:
        return handle_tool_flow(query, state)
    
    intent = classify(query)
    state["intent"] = intent
    
    if intent == "order_status":
        return start_tool_flow(state)
    
    return handle_rag(query, state)

async def handle_message_stream(query: str, state: dict) -> AsyncGenerator[str, None]:
    # 1. Continue tool workflow if active (Tools are usually non-streaming)
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
    query = query.lower()
    
    if any(k in query for k in ["order", "track", "package", "where is my"]):
        return "order_status"
    
    return "rag"