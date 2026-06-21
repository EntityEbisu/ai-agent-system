"""Typed agent state — the single source of truth for all agent data.

Replaces the old ``init_state() -> dict[str, Any]`` with an explicitly typed
``AgentState`` that LangGraph nodes read and write.  The ``messages`` field
uses LangGraph's ``add_messages`` reducer so conversation history is
auto-appended at every node transition.

All fields are optional via ``total=False`` — graph nodes fill them as they
execute, and the schema is a contract, not a constructor burden.
"""

from typing import Annotated, Any, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_ITERATIONS: int = 8
"""Hard cap on agent loop iterations to prevent runaway tool-calling loops."""

# ---------------------------------------------------------------------------
# Supporting types
# ---------------------------------------------------------------------------


class ToolCallAttempt(TypedDict, total=False):
    """A single tool invocation — name, arguments, and its outcome."""

    tool_name: str
    args: dict[str, Any]
    result: str | None
    error: str | None


# ---------------------------------------------------------------------------
# Agent state
# ---------------------------------------------------------------------------


class AgentState(TypedDict, total=False):
    """Runtime state for the LangGraph agent.

    Every field is optional so nodes can be written independently.  The
    ``messages`` field uses LangGraph's built-in ``add_messages`` reducer —
    append a message and it is automatically added to the list.
    """

    # -- Identity -----------------------------------------------------------

    user_id: str
    """Authenticated user identifier (set once at session start)."""

    session_id: str
    """Unique session identifier (set once at session start)."""

    # -- Conversation -------------------------------------------------------

    messages: Annotated[list[BaseMessage], add_messages]
    """Full conversation history.  LangGraph auto-appends via ``add_messages``."""

    # -- Control flow (output from the ``decide`` node) ---------------------

    next_action: Literal["tool_call", "ask_user", "final_answer", "error"]
    """What the LLM decided to do next — drives conditional graph edges."""

    reasoning: str
    """LLM's rationale for ``next_action``.  Logged for observability / trace."""

    # -- Tool execution -----------------------------------------------------

    pending_tool_call: ToolCallAttempt | None
    """A tool call that is being built across user turns (slot-filling).

    The LLM may need multiple turns to collect all required arguments.
    This field holds the partially-built call so the next ``decide`` round
    can resume it.
    """

    tool_calls_made: list[ToolCallAttempt]
    """All tool calls attempted in this session (successful or not).

    Used by the ``maybe_reflect`` node to diagnose repeated failures.
    """

    # -- RAG ----------------------------------------------------------------

    retrieved_context: str | None
    """Context retrieved from the knowledge base (if any).

    Set by a ``search_knowledge_base`` tool call; consumed by the
    ``compose`` node when formatting the final answer.
    """

    # -- Outcome ------------------------------------------------------------

    final_answer: str | None
    """The final response to present to the user."""

    errors: list[str]
    """Accumulated error messages across the graph run."""

    iteration: int
    """Current agent loop iteration.  Compared against ``MAX_ITERATIONS``."""
