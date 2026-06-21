"""Tool: search_knowledge_base — retrieves relevant documents from the knowledge base.

The LLM uses this when the user asks about policies, FAQs, or general
information about the company: "What's your return policy?", "How do I
cancel an order?", "Do you ship internationally?".
"""

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.exceptions import RetrieverError
from app.rag.retriever import get_retriever


class SearchKnowledgeBaseArgs(BaseModel):
    """Arguments for searching the knowledge base."""

    query: str = Field(
        ..., min_length=1, description="The search question or keywords"
    )
    k: int = Field(
        default=5, ge=1, le=20, description="Number of documents to retrieve (1–20)"
    )


class SearchKnowledgeBaseTool(BaseTool):
    """Search the company's knowledge base (FAQs, policies, documentation).

    Returns relevant excerpts that the assistant can use to answer the
    customer's question.  Each result includes the document text and its
    relevance score.
    """

    name: str = "search_knowledge_base"
    description: str = (
        "Search the company's knowledge base for FAQs, policies, and documentation. "
        "Use this when a customer asks about return policies, shipping information, "
        "cancellations, warranty, or any general company information. "
        "Returns relevant text excerpts ranked by similarity to the query."
    )
    args_schema: type[BaseModel] = SearchKnowledgeBaseArgs

    def _run(self, query: str, k: int = 5) -> str:
        """Execute the KB search synchronously."""
        try:
            retriever = get_retriever()
            docs = retriever.invoke(query)[:k]
        except RetrieverError as e:
            return f"Knowledge base is currently unavailable: {e}"
        except Exception as e:
            return f"Failed to search knowledge base: {e}"

        if not docs:
            return (
                "No relevant documents found in the knowledge base for that query. "
                "You may need to ask the customer to rephrase, or escalate to a human agent."
            )

        parts: list[str] = []
        for i, doc in enumerate(docs, start=1):
            source = doc.metadata.get("source", "unknown")
            parts.append(f"[{i}] (source: {source})\n{doc.page_content}")

        return "\n\n---\n\n".join(parts)

    async def _arun(self, query: str, k: int = 5) -> str:
        """Async variant delegates to sync."""
        return self._run(query=query, k=k)
