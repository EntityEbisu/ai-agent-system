"""Tool registry — single import point for all agent tools.

Usage::

    from app.agent.tools.registry import ALL_TOOLS, bind_tools

    llm_with_tools = bind_tools(some_llm)
    # or access the list directly:
    for tool in ALL_TOOLS:
        print(tool.name, tool.description)
"""

from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool

from .check_order_status import CheckOrderStatusTool
from .get_user_profile import GetUserProfileTool
from .search_knowledge_base import SearchKnowledgeBaseTool
from .update_shipping_address import UpdateShippingAddressTool

# ---------------------------------------------------------------------------
# Master tool list
# ---------------------------------------------------------------------------
# To add a new tool: import it above and append it to this list.  That's it.
# No other wiring needed — ``bind_tools`` picks up the list automatically.

ALL_TOOLS: list[BaseTool] = [
    CheckOrderStatusTool(),
    SearchKnowledgeBaseTool(),
    GetUserProfileTool(),
    UpdateShippingAddressTool(),
]

# ---------------------------------------------------------------------------
# One-liner binder
# ---------------------------------------------------------------------------


def bind_tools(llm: BaseLanguageModel) -> BaseLanguageModel:
    """Bind the full tool registry to an LLM so it can emit ``tool_calls``.

    Args:
        llm: A LangChain chat model instance.

    Returns:
        The same LLM with tools bound (via ``llm.bind_tools(...)``).
    """
    return llm.bind_tools(ALL_TOOLS)
