"""Structured-output schema for grounded RAG answers.

The ``Answer`` model enforces citation requirements and confidence
thresholds — the LLM cannot produce an uncited, low-confidence answer.
"""

from pydantic import BaseModel, Field


class Answer(BaseModel):
    """Structured output from the RAG pipeline.

    The LLM is required to fill every field.  The caller enforces the
    ``abstain`` and ``confidence`` checks at runtime.
    """

    answer: str = Field(
        ...,
        min_length=1,
        description="The final answer to the user's question, based solely on "
        "the provided context documents.",
    )
    citations: list[str] = Field(
        ...,
        description="Document IDs (from the context) that support the answer. "
        "Each element should be a document_id or source path. "
        "MUST be non-empty when ``abstain`` is ``False``.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the answer based on the available context "
        "(0.0 = no confidence, 1.0 = certain).",
    )
    abstain: bool = Field(
        ...,
        description="If ``True``, the answer field should contain an explanation "
        "of why the question cannot be answered from the available context, "
        "and ``citations`` should be empty.",
    )
    reason_for_abstention: str | None = Field(
        default=None,
        description="Required when ``abstain`` is ``True``.  Explain what "
        "information is missing that would be needed to answer the question.",
    )
