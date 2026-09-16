"""
Domain Exceptions - Business Rule Violations

What it does:
    Defines exception classes that represent violations of business rules
    in the domain layer.

Why:
    Domain exceptions separate "what went wrong in the business logic" from
    "what went wrong in the infrastructure". This allows the application layer
    to catch domain-specific errors and respond appropriately.
"""

from __future__ import annotations


class TikTikDomainException(Exception):
    """Base exception for all domain layer errors."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message}"


class InvalidEntityDataException(TikTikDomainException):
    """Raised when entity construction data is invalid or incomplete."""


class EntityNotFoundException(TikTikDomainException):
    """Raised when a requested entity (video, user, etc.) does not exist."""


class SessionPoolExhaustedException(TikTikDomainException):
    """Raised when no valid browser sessions are available for a request."""


class RequestFailedException(TikTikDomainException):
    """Raised when a request to TikTik's API fails after all retries."""

    def __init__(self, message: str, url: str = "", status_code: int | None = None, **kwargs):
        super().__init__(message, details={"url": url, "status_code": status_code, **kwargs})


class ResponseParsingException(TikTikDomainException):
    """Raised when a response from TikTik cannot be parsed into domain objects."""


class RateLimitedException(TikTikDomainException):
    """Raised when TikTik rate-limits requests."""


class BotDetectionException(TikTikDomainException):
    """Raised when TikTik detects automated/bot behavior."""
