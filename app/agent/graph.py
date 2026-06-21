"""LangGraph-based ReAct agent — tool-calling orchestration with structured
decision-making and automatic error recovery.

Topology
--------
  START → decide ──┬─ tool_call  → run_tool → decide (loop back)
                    ├─ ask_user   → END (wait for next turn)
                    ├─ final_answer → compose → END
                    └─ iteration ≥ MAX_ITERATIONS → error → END

Every turn the LLM emits a ``Decision`` struct (see ``app.agent.schemas``).
The graph reads ``Decision.next`` to select the next node.
"""

from typing import Any, Literal

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph

from app.agent.schemas import Decision
from app.agent.state import MAX_ITERATIONS, AgentState
from app.agent.tools.registry import ALL_TOOLS
from app.services.llm import get_llm

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a helpful customer support assistant for an e-commerce store.
Your job is to help customers with orders, account questions, and company policies.

You have access to the following tools:

{tool_descriptions}

You must respond with a structured Decision. Follow these rules:

1. **tool_call** — If the customer's request requires data you don't have (order
   status, user profile, KB article), call the appropriate tool. Set
   ``next="tool_call"`` and fill in ``tool_name`` and ``tool_args`` with the
   arguments the customer provided. **Do not make up arguments.** If the customer
   hasn't provided all required arguments, set ``next="ask_user"`` and ask for
   the missing information.

2. **ask_user** — If you need more information from the customer (e.g. missing
   order details, clarification), set ``next="ask_user"`` and provide a clear,
   polite question in ``question_for_user``.

3. **final_answer** — If the conversation is complete and you can answer the
   customer's question, set ``next="final_answer"``. Include the full answer
   in your reasoning (it will be delivered as the response).

Important rules:
- Always verify identity before revealing order or account information.
- When a customer asks "Where is my package?" or similar, use ``check_order_status``.
- When they ask about policies, returns, shipping, use ``search_knowledge_base``.
- When they ask about their account or address, use ``get_user_profile``.
- When they want to change their address, use ``update_shipping_address``.
- Be polite, professional, and concise.
- If a tool returns an error, explain the issue and ask the customer to verify.
- If you cannot help after 2 attempts, suggest escalating to a human agent."""


def _tool_descriptions() -> str:
    """Build a textual tool registry for the system prompt."""
    parts: list[str] = []
    for tool in ALL_TOOLS:
        schema = tool.args_schema.model_json_schema() if tool.args_schema else {}
        props = schema.get("properties", {})
        required = set(schema.get("required", []))
        field_lines: list[str] = []
        for name, info in props.items():
            flags = "required" if name in required else f"optional (default={info.get('default', 'N/A')})"
            desc = info.get("description", "")
            field_lines.append(f"    {name} ({flags}): {desc}")
        fields_str = "\n".join(field_lines) if field_lines else "    (no arguments)"
        parts.append(f"  - {tool.name}: {tool.description}\n{fields_str}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_CACHED: str | None = None


def _build_system_prompt() -> str:
    """Build the system prompt with embedded tool descriptions (cached)."""
    global _SYSTEM_PROMPT_CACHED
    if _SYSTEM_PROMPT_CACHED is None:
        _SYSTEM_PROMPT_CACHED = SYSTEM_PROMPT.format(
            tool_descriptions=_tool_descriptions()
        )
    return _SYSTEM_PROMPT_CACHED


def _build_decide_chain():
    """Build the LLM chain that produces a ``Decision`` struct.

    The model sees the system prompt + conversation history and outputs
    a structured ``Decision`` object.
    """
    llm = get_llm(streaming=False)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _build_system_prompt()),
            ("placeholder", "{messages}"),
        ]
    )
    return prompt | llm.with_structured_output(Decision)


def _build_compose_chain():
    """Build the LLM chain that formats the final answer.

    The model sees the system prompt + conversation history (including tool
    results) and generates a natural-language response for the customer.
    """
    llm = get_llm(streaming=False)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _build_system_prompt()),
            ("placeholder", "{messages}"),
        ]
    )
    return prompt | llm


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------


def decide_node(state: AgentState) -> dict[str, Any]:
    """Ask the LLM what to do next.

    Returns a ``Decision`` struct that the conditional edge uses to route
    to the next node.
    """
    chain = _build_decide_chain()
    messages = state.get("messages", [])

    decision = chain.invoke({"messages": messages})

    return {
        "decision": decision,
        "reasoning": decision.reasoning,
        "iteration": state.get("iteration", 0) + 1,
    }


def run_tool_node(state: AgentState) -> dict[str, Any]:
    """Execute the tool selected by the LLM and return the result.

    The result is appended to ``messages`` as a ``ToolMessage`` so the
    next ``decide`` invocation can see it.
    """
    decision: Decision | None = state.get("decision")  # type: ignore[assignment]
    if not decision or decision.next != "tool_call":
        return {}

    tool_name = decision.tool_name or ""
    tool_args = decision.tool_args or {}

    # Find the tool in the registry
    tool = next(
        (t for t in ALL_TOOLS if t.name == tool_name),
        None,
    )

    tool_call_id = f"tc_{state.get('iteration', 0)}"

    if tool is None:
        error_msg = f"Unknown tool '{tool_name}'. Available tools: {[t.name for t in ALL_TOOLS]}"
        return {
            "messages": [
                ToolMessage(
                    content=error_msg,
                    tool_call_id=tool_call_id,
                )
            ],
        }

    # Execute the tool
    try:
        result = tool.run(tool_args)
        return {
            "messages": [
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call_id,
                )
            ],
        }
    except Exception as e:
        error_msg = f"Tool '{tool_name}' returned an error: {e}"
        return {
            "messages": [
                ToolMessage(
                    content=error_msg,
                    tool_call_id=tool_call_id,
                )
            ],
        }


def compose_node(state: AgentState) -> dict[str, Any]:
    """Generate the final answer to the customer.

    Uses the LLM with the full conversation history (including tool results)
    to produce a natural-language response.
    """
    chain = _build_compose_chain()
    messages = state.get("messages", [])

    result = chain.invoke({"messages": messages})

    final_answer = result.content if hasattr(result, "content") else str(result)
    return {
        "final_answer": final_answer,
        "messages": [AIMessage(content=final_answer)],
    }


def error_node(state: AgentState) -> dict[str, Any]:
    """Handle the case where the agent exceeded MAX_ITERATIONS.

    Returns a friendly message instead of an infinite loop or 500.
    """
    final_answer = (
        "I'm having trouble completing this request. "
        "Please try again or rephrase your question. "
        "If the issue persists, a human agent will be able to help."
    )
    return {
        "final_answer": final_answer,
        "messages": [AIMessage(content=final_answer)],
    }


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def route_decision(state: AgentState) -> Literal["run_tool", "compose", "error", "__end__"]:
    """Route based on the LLM's decision.

    Checks the iteration cap first, then reads ``Decision.next``.
    """
    if state.get("iteration", 0) >= MAX_ITERATIONS:
        return "error"

    decision: Decision | None = state.get("decision")  # type: ignore[assignment]
    if decision is None:
        return "error"

    if decision.next == "tool_call":
        return "run_tool"
    elif decision.next == "final_answer":
        return "compose"
    else:
        # ask_user — yield control back to the caller
        return "__end__"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_graph() -> StateGraph:
    """Build and return the compiled agent :class:`StateGraph`."""
    builder = StateGraph(AgentState)

    builder.add_node("decide", decide_node)
    builder.add_node("run_tool", run_tool_node)
    builder.add_node("compose", compose_node)
    builder.add_node("error", error_node)

    builder.add_edge(START, "decide")

    builder.add_conditional_edges(
        "decide",
        route_decision,
        {
            "run_tool": "run_tool",
            "compose": "compose",
            "error": "error",
            "__end__": END,
        },
    )

    # Tool loop: after running a tool, go back to decide
    builder.add_edge("run_tool", "decide")
    builder.add_edge("compose", END)
    builder.add_edge("error", END)

    return builder.compile()


# Pre-built singleton for import convenience
agent_graph = build_graph()
