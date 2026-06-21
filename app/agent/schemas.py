"""Pydantic schemas for agent orchestration — the structured contract
between the LLM and the LangGraph runtime.

The ``Decision`` model is the LLM's structured output.  Every turn, the
LLM emits a ``Decision``, and the graph's conditional edges branch on
``Decision.next``.
"""

from pydantic import BaseModel, Field


class Decision(BaseModel):
    """Structured output from the LLM — what to do next and why.

    The LLM emits exactly one ``Decision`` per turn after seeing the
    conversation history and the tool registry.  The graph reads
    ``next`` to decide which node to route to.
    """

    next: str = Field(
        ...,
        pattern=r"^(tool_call|ask_user|final_answer)$",
        description="What the agent should do next: 'tool_call' to invoke a tool, "
        "'ask_user' to wait for the user's response, 'final_answer' to deliver the response.",
    )
    reasoning: str = Field(
        ...,
        min_length=1,
        description="The LLM's reasoning for this decision. "
        "Logged for observability and traceability.",
    )
    tool_name: str | None = Field(
        default=None,
        description="Name of the tool to call (required when next='tool_call').",
    )
    tool_args: dict | None = Field(
        default=None,
        description="Arguments for the tool call (required when next='tool_call').",
    )
    question_for_user: str | None = Field(
        default=None,
        description="Question to ask the user (required when next='ask_user').",
    )
