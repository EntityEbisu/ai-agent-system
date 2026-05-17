# runtime_callgraph.md

```
GET /chat (app/main.py -> chat endpoint)
    └─ get_session (app/agent/memory.py) → init_state (app/agent/state.py)
    └─ logger = get_logger_instance (app/main.py -> app/services/observability.py)
    └─ persist_message (app/main.py) → DB write (app/data/models.py)
    └─ handle_message_stream (app/agent/router.py)
        ├─ if tool_state.active → handle_tool_flow (app/agent/workflow.py)
        └─ else classify → intent
            ├─ intent == "order_status" → start_tool_flow (app/agent/workflow.py)
            └─ otherwise → handle_rag_stream (app/rag/pipeline.py)
                ├─ get_retriever (app/rag/retriever.py) → vector store lookup
                ├─ get_llm(streaming=True) (app/services/llm.py)
                └─ chain.astream → yields token chunks
    └─ after stream finishes:
        ├─ record latency (metrics.get_summary())
        ├─ estimate token counts (simple length //4)
        ├─ logger.log_response (app/services/observability.py)
        └─ persist_message (assistant response) → DB write
```

The graph only includes code paths that are executed at runtime (Tier 1). No indirect imports or unused modules are shown.
