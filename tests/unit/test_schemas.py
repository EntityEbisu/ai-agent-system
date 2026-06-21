"""Unit tests for agent schemas (Decision model)."""
import pytest
from pydantic import ValidationError

from app.agent.schemas import Decision


class TestDecision:
    def test_final_answer_decision(self):
        d = Decision(next="final_answer", reasoning="Order found, delivering response.")
        assert d.next == "final_answer"
        assert d.reasoning.startswith("Order found")

    def test_tool_call_decision(self):
        d = Decision(
            next="tool_call",
            reasoning="Need user profile",
            tool_name="get_user_profile",
            tool_args={"user_id": "u1"},
        )
        assert d.tool_name == "get_user_profile"
        assert d.tool_args == {"user_id": "u1"}

    def test_ask_user_decision(self):
        d = Decision(
            next="ask_user",
            reasoning="Missing order ID",
            question_for_user="What is your order number?",
        )
        assert d.question_for_user == "What is your order number?"

    def test_default_optional_fields(self):
        d = Decision(next="final_answer", reasoning="Done")
        assert d.tool_name is None
        assert d.tool_args is None
        assert d.question_for_user is None

    def test_invalid_next_value_raises(self):
        with pytest.raises(ValidationError):
            Decision(next="invalid_value", reasoning="test")

    def test_empty_reasoning_raises(self):
        with pytest.raises(ValidationError):
            Decision(next="final_answer", reasoning="")
