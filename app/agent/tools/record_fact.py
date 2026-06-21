"""Tool: record_fact — store a learned fact about the user in semantic memory.

The agent calls this when it learns something about the user that should be
remembered across sessions (shipping address, VIP status, preferences, …).
"""

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.memory.semantic import SemanticMemory


class RecordFactArgs(BaseModel):
    """Arguments for storing a user fact."""

    key: str = Field(
        ..., min_length=1, max_length=128,
        description="Fact key (e.g. 'preferred_shipping_address', 'is_vip'). "
        "Use snake_case and be consistent across calls.",
    )
    value: str = Field(
        ..., min_length=1, max_length=512,
        description="Fact value (e.g. '123 Main St', 'true').",
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0,
        description="How confident you are in this fact (0.0–1.0). "
        "Only store facts you are quite sure about (>= 0.8).",
    )


class RecordFactTool(BaseTool):
    """Record a fact about the user that should persist across sessions.

    Use this when the user explicitly states a preference, provides their
    address, or otherwise offers information worth remembering.
    """

    name: str = "record_fact"
    description: str = (
        "Store information about the user that should be remembered across "
        "conversations. Use for shipping addresses, preferences, account "
        "details, or any fact the user explicitly provides."
    )
    args_schema: type[BaseModel] = RecordFactArgs  # type: ignore[assignment]

    def _run(self, key: str, value: str, confidence: float = 1.0) -> str:
        return f"Fact recording prepared. key={key}, value={value}, confidence={confidence}"

    async def _arun(self, key: str, value: str, confidence: float = 1.0) -> str:
        return self._run(key=key, value=value, confidence=confidence)
