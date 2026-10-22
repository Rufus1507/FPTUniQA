"""Custom exceptions and resilience mechanisms (retry, circuit breaker) for FPTUniQA."""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, Tuple, Type, TypeVar

from FPTUniQA.utils.logger import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


# =====================================================================
# Custom Exceptions Hierarchy
# =====================================================================

class FPTUniQAError(Exception):
    """Base exception for all FPTUniQA errors."""
    pass


class RetrievalError(FPTUniQAError):
    """Raised when an error occurs during dense, BM25, or hybrid retrieval."""
    pass


class LLMError(FPTUniQAError):
    """Raised when an error occurs while communicating with LLM services."""
    pass


class ConfigurationError(FPTUniQAError):
    """Raised when configuration validation or loading fails."""
    pass


class IndexingError(FPTUniQAError):
    """Raised when indexing or index loading fails."""
    pass


class CircuitBreakerOpenError(FPTUniQAError):
    """Raised when an operation is attempted while the circuit breaker is OPEN."""
    pass


# =====================================================================
# Resilience: Retry with Exponential Backoff
# =====================================================================

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator to retry a function call with exponential backoff."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = base_delay
            last_exception: Exception | None = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exception = exc
                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} attempts: {exc}"
                        )
                        raise
                    logger.warning(
                        f"Attempt {attempt}/{max_retries} for {func.__name__} failed ({exc}). "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
            if last_exception:
                raise last_exception
        return wrapper  # type: ignore[return-value]
    return decorator


# =====================================================================
# Resilience: Circuit Breaker Pattern
# =====================================================================

class CircuitBreaker:
    """Circuit breaker pattern to protect external services from cascade failures."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        name: str = "default",
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_state_change = time.monotonic()

    def __call__(self, func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self._check_state()
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as exc:
                self._on_failure(exc)
                raise
        return wrapper  # type: ignore[return-value]

    def _check_state(self) -> None:
        now = time.monotonic()
        if self.state == self.OPEN:
            if now - self.last_state_change >= self.recovery_timeout:
                logger.info(f"CircuitBreaker [{self.name}] entering HALF_OPEN state.")
                self.state = self.HALF_OPEN
                self.last_state_change = now
            else:
                remaining = self.recovery_timeout - (now - self.last_state_change)
                raise CircuitBreakerOpenError(
                    f"CircuitBreaker [{self.name}] is OPEN. Retry in {remaining:.1f}s."
                )

    def _on_success(self) -> None:
        if self.state == self.HALF_OPEN:
            logger.info(f"CircuitBreaker [{self.name}] recovered to CLOSED state.")
        self.state = self.CLOSED
        self.failure_count = 0

    def _on_failure(self, exc: Exception) -> None:
        self.failure_count += 1
        now = time.monotonic()
        logger.warning(
            f"CircuitBreaker [{self.name}] recorded failure #{self.failure_count}: {exc}"
        )
        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN
            self.last_state_change = now
            logger.error(
                f"CircuitBreaker [{self.name}] tripped to OPEN state for {self.recovery_timeout}s."
            )
