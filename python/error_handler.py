"""
Robust Error Handling and Resilience Strategies for LLM APIs.
Defines specific exception hierarchies, exponential backoff retries with jitter,
and diagnostic error classification.
"""

import time
import random
import functools
import logging
from typing import Callable, Type, Tuple, Optional, Any

logger = logging.getLogger("LLMErrorHandler")


class LLMAPIError(Exception):
    """Base exception for all LLM API failures."""
    def __init__(self, message: str, status_code: Optional[int] = None, hint: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.hint = hint or "Check your network connection and configuration."

    def __str__(self):
        base = f"[{self.status_code}] {self.message}" if self.status_code else self.message
        if self.hint:
            return f"{base} | Hint: {self.hint}"
        return base


class LLMAuthenticationError(LLMAPIError):
    """Raised when API key is missing, invalid, or expired (HTTP 401/403)."""
    def __init__(self, message: str = "Invalid or missing LLM API credentials."):
        super().__init__(
            message=message,
            status_code=401,
            hint="Verify that your OPENAI_API_KEY or GEMINI_API_KEY is correctly set in .env.",
        )


class LLMRateLimitError(LLMAPIError):
    """Raised when rate limits or quotas are exceeded (HTTP 429)."""
    def __init__(self, message: str = "LLM API Rate limit or quota exhausted."):
        super().__init__(
            message=message,
            status_code=429,
            hint="Back off requests, check your provider billing tier, or switch to a fallback model.",
        )


class LLMContextLengthExceededError(LLMAPIError):
    """Raised when prompt + max_tokens exceeds model context limits (HTTP 400)."""
    def __init__(self, message: str = "Conversation history exceeds model context window."):
        super().__init__(
            message=message,
            status_code=400,
            hint="Use the conversation sliding window or increase max_context_tokens.",
        )


class LLMConnectionError(LLMAPIError):
    """Raised when network timeout, DNS resolution failure, or server 5xx occurs."""
    def __init__(self, message: str = "Failed to communicate with LLM provider server."):
        super().__init__(
            message=message,
            status_code=503,
            hint="Check internet connectivity or provider service status page.",
        )


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (LLMRateLimitError, LLMConnectionError, TimeoutError),
):
    """
    Decorator executing wrapped function with exponential backoff and jitter.
    Guarantees resilient retries for transient HTTP 429 and network failures.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception: Optional[Exception] = None

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as ex:
                    last_exception = ex
                    if attempt == max_retries:
                        logger.error(f"[Retry Exhausted] Attempt {attempt}/{max_retries} failed: {ex}")
                        raise

                    # Calculate delay with randomized jitter to prevent thundering herd
                    sleep_time = delay * (1.0 + (random.random() * 0.2 if jitter else 0.0))
                    logger.warning(
                        f"[Transient Error] Attempt {attempt}/{max_retries} failed ({type(ex).__name__}). "
                        f"Retrying in {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    delay *= backoff_factor

            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def classify_api_exception(ex: Exception) -> LLMAPIError:
    """
    Translates third-party provider exceptions (e.g. from openai, google.genai, requests)
    into standard domain exceptions.
    """
    err_str = str(ex).lower()
    if "auth" in err_str or "unauthorized" in err_str or "api_key" in err_str or "401" in err_str:
        return LLMAuthenticationError(str(ex))
    if "rate" in err_str or "quota" in err_str or "429" in err_str:
        return LLMRateLimitError(str(ex))
    if "context" in err_str or "maximum context" in err_str or "too long" in err_str:
        return LLMContextLengthExceededError(str(ex))
    if "timeout" in err_str or "connection" in err_str or "503" in err_str:
        return LLMConnectionError(str(ex))
    return LLMAPIError(f"Unexpected API error: {ex}")
