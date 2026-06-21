"""Unit tests for tool registry."""
from app.agent.tools.registry import ALL_TOOLS, bind_tools


class TestToolRegistry:
    def test_all_tools_is_list(self):
        assert isinstance(ALL_TOOLS, list)
        assert len(ALL_TOOLS) > 0

    def test_tools_have_name_and_description(self):
        for tool in ALL_TOOLS:
            assert tool.name, f"Tool missing name: {tool}"
            assert tool.description, f"Tool missing description: {tool.name}"

    def test_tool_names_are_unique(self):
        names = [t.name for t in ALL_TOOLS]
        assert len(names) == len(set(names)), "Duplicate tool names found"

    def test_tool_names(self):
        """All expected tools should be present."""
        tool_names = [t.name for t in ALL_TOOLS]
        expected = [
            "check_order_status",
            "search_knowledge_base",
            "get_user_profile",
            "update_shipping_address",
            "record_fact",
            "recall_facts",
        ]
        for name in expected:
            assert name in tool_names, f"Missing tool: {name}"
