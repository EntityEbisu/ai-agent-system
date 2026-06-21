"""Tool: recall_facts — retrieve stored facts about the current user.

The agent calls this when it needs to remember something about the user
(shipping address, preferences, account tier, …).
"""

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.memory.semantic import SemanticMemory


class RecallFactsArgs(BaseModel):
    """Arguments for recalling user facts."""

    key_prefix: str = Field(
        default="",
        description="Optional filter — only return facts whose key starts "
        "with this prefix.  Leave empty to return all facts.",
    )


class RecallFactsTool(BaseTool):
    """Recall stored facts about the current user.

    Use this when you need information you learned in a previous conversation
    — shipping address, preferences, account status, etc.
    """

    name: str = "recall_facts"
    description: str = (
        "Retrieve stored information about the current user from previous "
        "conversations. Use when the user asks 'You should know my address' "
        "or 'Remember my preference from last time'."
    )
    args_schema: type[BaseModel] = RecallFactsArgs  # type: ignore[assignment]

    def _run(self, key_prefix: str = "") -> str:
        return (
            f"Fact recall prepared. key_prefix='{key_prefix or '(all)'}' "
            "(user_id will be injected by the graph node.)"
        )

    async def _arun(self, key_prefix: str = "") -> str:
        return self._run(key_prefix=key_prefix)
