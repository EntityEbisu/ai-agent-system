"""Unit tests for agent state types."""
import pytest
from langchain_core.messages import HumanMessage, AIMessage

from app.agent.state import AgentState, ToolCallAttempt, MAX_ITERATIONS


class TestConstants:
    def test_max_iterations(self):
        assert MAX_ITERATIONS == 8


class TestToolCallAttempt:
    def test_minimal_tool_call(self):
        tca = ToolCallAttempt(tool_name="get_user_profile")
        assert tca["tool_name"] == "get_user_profile"

    def test_full_tool_call(self):
        tca = ToolCallAttempt(
            tool_name="check_order_status",
            args={"order_id": "123"},
            result="Shipped",
        )
        assert tca["args"] == {"order_id": "123"}
        assert tca["result"] == "Shipped"
