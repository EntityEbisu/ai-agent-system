"""Application exception types for typed error handling.

Each exception carries a ``user_message`` that is safe to return
to the client and a ``log_message`` with internal details.
"""


class AppError(Exception):
    """Base application error with user-safe and log-only messages."""

    def __init__(self, user_message: str, log_message: str | None = None):
        self.user_message = user_message
        self.log_message = log_message or user_message
        super().__init__(self.log_message)


class LLMConfigError(AppError):
    """LLM configuration is missing or invalid — not retryable."""

    def __init__(self, detail: str = ""):
        super().__init__(
            user_message="The AI service is not configured. Please check your API keys.",
            log_message=f"LLM configuration error: {detail}",
        )


class LLMTimeoutError(AppError):
    """LLM call exceeded its deadline."""

    def __init__(self, timeout_s: int = 30):
        super().__init__(
            user_message="The AI service took too long to respond. Please try again.",
            log_message=f"LLM call timed out after {timeout_s}s",
        )


class LLMRetryableError(AppError):
    """LLM call failed transiently (rate limit, server error)."""

    def __init__(self, status: int = 0, detail: str = ""):
        super().__init__(
            user_message="The AI service is temporarily unavailable. Please try again.",
            log_message=f"LLM retryable error (HTTP {status}): {detail}",
        )


class RetrieverError(AppError):
    """Knowledge base is unavailable."""

    def __init__(self, detail: str = ""):
        super().__init__(
            user_message="The knowledge base is currently unavailable.",
            log_message=f"Retriever error: {detail}",
        )


class WorkflowError(AppError):
    """Workflow execution encountered an unexpected error."""

    def __init__(self, detail: str = ""):
        super().__init__(
            user_message="Something went wrong. Please try again.",
            log_message=f"Workflow error: {detail}",
        )
