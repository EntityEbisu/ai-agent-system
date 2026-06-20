# Phase B — Rebuild the Agent (Weeks 2–4)

**Theme:** Give the LLM real agency. Replace the keyword router and the hard-coded state machine with a typed, tool-calling, graph-based agent loop.

**Entry criteria:** All Phase A checklist items are green. You have a service that doesn't lie about what it is, doesn't lose state, and doesn't leak PII.

**Exit criteria:** A working `StateGraph` that the LLM drives end-to-end. The `app/agent/router.py` / `workflow.py` / `state.py` files are deleted. The LLM decides when to call a tool, when to ask the user, and when to give a final answer.

---

## Step 7: Define a typed agent state

**What:**
- The current `state` is a `dict[str, Any]` that is mutated in place and passed by reference across handlers. Replace it with a `TypedDict` (or Pydantic `BaseModel`) that LangGraph nodes can read and write explicitly.
- Proposed schema:
  ```python
  from typing import Annotated
  from langgraph.graph.message import add_messages
  from langchain_core.messages import BaseMessage

  class AgentState(TypedDict, total=False):
      # Conversation
      messages: Annotated[list[BaseMessage], add_messages]
      user_id: str
      session_id: str

      # Control
      plan: list[Step]
      current_step: int
      next_action: Literal["tool_call", "ask_user", "final_answer", "error"]

      # Tool execution
      tool_calls_made: list[ToolCall]
      tool_results: list[ToolResult]
      pending_tool_call: ToolCall | None

      # RAG
      memory_hits: list[Document]
      retrieved_context: str | None

      # Outcome
      final_answer: str | None
      errors: list[AgentError]
      iteration: int
  ```
- Add a `MAX_ITERATIONS = 8` guard in the state so a runaway loop terminates.
- Make sure the state is serializable. JSON-serialize it on the way into Redis (Step 3 from Phase A) and JSON-deserialize on the way out.

**Pattern:** Explicit state schema · Reducers for list fields (LangGraph's `add_messages` is the canonical pattern) · Bounded resources.

**Library:** `pydantic` v2 for validation, `langgraph` (`StateGraph`, `add_messages` reducer), `typing_extensions.TypedDict`.

**Acceptance:** `AgentState` is the only state object passed between nodes. `state["messages"]` is the only place conversation history lives. The schema is enforced on load from Redis.

---

## Step 8: Tool registry + semantic tool-calling

**What:**
- Create `app/agent/tools/` package. Each tool is a `BaseTool` (or `@tool` decorator) with a docstring-derived description and a Pydantic args schema. The docstring is what the LLM sees; write them as if you were writing a manual entry for an agent, not for a developer.
- Examples to ship:
  - `check_order_status(name: str, ssn_last4: str, dob: str) -> OrderStatus`
  - `search_knowledge_base(query: str, k: int = 5) -> list[DocumentChunk]`
  - `get_user_profile(user_id: str) -> UserProfile`
  - `update_shipping_address(user_id: str, address: Address) -> Confirmation`
- A `app/agent/tools/registry.py` exposes `ALL_TOOLS: list[BaseTool]` and a `bind_tools(llm)` helper.
- The LLM sees the tools via `llm.bind_tools(ALL_TOOLS)`. It emits a structured `tool_calls` array. The orchestrator (Step 10) parses the array, dispatches each call, and feeds the result back as a `ToolMessage` so the next LLM call sees it.
- **Replace the 1-line mock** `app/tools/order_status.py` with a real implementation. For the demo, a local SQLite `orders` table seeded with fake data is fine; for production, an HTTP client to the real order service with retries and a circuit breaker. The important thing: the tool's `run()` is no longer a hard-coded return string.

**Pattern:** LLM-as-controller · Semantic tool selection · Tool abstraction · Declarative schemas (Pydantic args).

**Library:** `langchain_core.tools.tool`, `langchain_core.tools.BaseTool`, `ChatOpenAI.bind_tools`, Pydantic for args.

**Acceptance:** `llm_with_tools = llm.bind_tools(ALL_TOOLS)`. A free-form user message like `"Where is my package?"` causes the LLM to emit a `tool_call` for `check_order_status` with the relevant args. A message like `"What's our return policy?"` causes the LLM to call `search_knowledge_base`. The wiring is data-driven: adding a new tool is one line in `registry.py`.

---

## Step 9: Replace the keyword router with an LLM classifier (or skip it entirely)

**What:**
- **Option A — keep a lightweight first-stage router.** A small/cheap model (`gpt-4o-mini`, or a local zero-shot classifier like `MoritzLaurer/deberta-v3-large-zeroshot-v2.0`) picks a high-level track: `tool_call` vs. `knowledge_qa` vs. `chitchat`. Then the second stage is specialized. Pro: cheap. Con: still deterministic-shaped, and you have to maintain the labels.
- **Option B — drop the router entirely (recommended).** Let the LLM see the full tool set and the user's history. Constrain its decision with structured output:
  ```python
  class Decision(BaseModel):
      next: Literal["tool_call", "ask_user", "final_answer"]
      reasoning: str  # shown to the user in /trace
      tool_name: str | None
      tool_args: dict | None
      question_for_user: str | None
  ```
  The orchestrator (Step 10) acts on `Decision.next`. The `reasoning` field becomes your observability surface — every decision the agent makes is now an LLM-emitted string you can log, search, and replay.
- Delete `app/agent/router.py::classify` and `handle_message` / `handle_message_stream`. They are replaced by the orchestrator.

**Pattern:** LLM-driven control flow · Plan-and-Execute or ReAct · Structured outputs as the API between LLM and runtime.

**Library:** `langchain_core.prompts.ChatPromptTemplate` with `.with_structured_output(Decision)`, `pydantic` v2 for the `Decision` schema.

**Acceptance:** `grep "in query" app/agent/` returns nothing. The first thing the LLM sees in any turn is the full tool registry + the user message + the prior `messages` list. It returns a `Decision` object. The orchestrator (Step 10) consumes it.

---

## Step 10: Implement a ReAct / Plan-and-Execute loop with LangGraph

**What:**
- Build a `StateGraph` in `app/agent/graph.py`:
  ```
  START
    → load_memory          (read working memory from Redis, fetch top-k episodic memory)
    → decide               (LLM with structured output → Decision)
    → branch on Decision.next:
        "tool_call"   → run_tool     → maybe_reflect  → decide
        "ask_user"    → ask_user     → END (yield question, wait for next turn)
        "final_answer"→ compose      → persist        → END
        "error"       → recover      → decide
  ```
- Each node is a small function:
  - `decide(state) -> {"decision": Decision}`
  - `run_tool(state) -> {"tool_results": [...], "iteration": state["iteration"] + 1}`
  - `maybe_reflect(state) -> {"decision": Decision}` — on tool error, ask the LLM to diagnose and propose a fallback
  - `compose(state) -> {"final_answer": str, "messages": [...]}`
- Termination: `iteration >= MAX_ITERATIONS` OR `next == "final_answer"`. Add an explicit error node that emits `"I'm having trouble completing this. Please try again or rephrase."` on the iteration cap.
- The `messages` reducer (`add_messages`) appends each turn automatically; you do not need to manage the list manually.
- Persist the final state back to Redis at every node boundary (or use a checkpointer; LangGraph has `MemorySaver` / `PostgresSaver`).

**Pattern:** ReAct / Plan-and-Execute · Explicit state machine · Graph-based orchestration · Reflection on error.

**Library:** `langgraph` (`StateGraph`, `add_conditional_edges`, `START`, `END`), `langgraph.checkpoint.memory.MemorySaver` for dev, `langgraph.checkpoint.postgres.PostgresSaver` for prod.

**Acceptance:**
- `graph.compile()` returns a runnable.
- `graph.invoke({"messages": [HumanMessage("Where is my package?")], "user_id": "u1", "session_id": "s1", "iteration": 0})` returns a state with `final_answer` set, after at least one `run_tool` invocation.
- A simulated tool error (e.g., a tool that always raises) causes `maybe_reflect` to be invoked; the agent either retries, asks the user, or terminates with a friendly error — never a 500.
- A trace export (LangSmith or local OTLP) shows the full graph execution with each node's inputs/outputs.

---

## Step 11: Replace the rigid slot-filling workflow with a tool-call

**What:**
- **Delete `app/agent/workflow.py` entirely.** It is antithetical to the goal. Do not refactor it; replace it.
- The order-status "flow" is now a single tool (`check_order_status`) with Pydantic args: `name: str`, `ssn_last4: str = Field(min_length=4, max_length=4, pattern=r"^\d{4}$")`, `dob: date`. Pydantic enforces the constraints before the tool runs — the `valid_ssn` / `valid_dob` helpers in `workflow.py` are no longer needed.
- The LLM, on receiving the user's first message, decides it needs `check_order_status`. The tool's args schema is missing `name`. The LLM sees the missing arg in the tool spec and asks the user for it naturally. On the next turn, the LLM again calls the tool, this time missing `ssn_last4`. The dialog is the LLM's, not a Python state machine's.
- Where the old code stored `state["tool_state"]["collected"]`, the new code stores the partial args in `AgentState.pending_tool_call` or reconstructs the call each turn. The point: **the schema is the source of truth, not a parallel Python dict.**

**Pattern:** LLM-driven slot filling via tool-calling args · Declarative schemas · Schema as the contract.

**Library:** `langchain_core.tools.BaseTool` with `args_schema: type[BaseModel]`, Pydantic `Field(..., min_length=..., pattern=...)`.

**Acceptance:** The order-status conversation still completes successfully, but the dialog text is generated by the LLM (slightly different each run). Adding a new required field to the tool (e.g., `email`) causes the LLM to ask for `email` without any code change. An invalid SSN (5 digits) is rejected by Pydantic with a clear error message that the LLM uses to ask the user to retry.

---

## End-of-Phase Checklist

- [ ] `app/agent/state.py` exports a `TypedDict` `AgentState` (the old `init_state` is gone)
- [ ] `app/agent/router.py` is deleted; `app/agent/workflow.py` is deleted
- [ ] `app/agent/tools/` contains a `registry.py` exposing `ALL_TOOLS: list[BaseTool]`
- [ ] Every tool has a Pydantic `args_schema` and a real (or at least plausibly real) `run()` implementation
- [ ] `app/agent/graph.py` defines and compiles a `StateGraph` with the topology above
- [ ] The graph terminates within `MAX_ITERATIONS` on every test
- [ ] LangSmith (or local OTLP) trace export is wired and shows full graph execution
- [ ] A 50-turn golden eval set (`eval/golden_conversations.jsonl`) passes ≥90% — use `deepeval` or `langsmith.evaluate`

When all of these are green, proceed to **Phase C** (`audit-phase-C.md`).
