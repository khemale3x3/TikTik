"""
Exceptions - Error Hierarchy

What it does:
    Defines the exception hierarchy for the library. All exceptions inherit
    from TikTikException, providing a consistent error handling interface.

How it works:
    Each exception carries:
    - raw_response: The raw response that caused the error
    - message: Human-readable error description
    - error_code: Optional numeric error code from TikTik

    The __str__ method formats as "{error_code} -> {message}" for easy logging.

Why:
    Structured exceptions allow consumers to:
    - Catch specific error types (e.g., EmptyResponseException for bot detection)
    - Access raw response data for debugging
    - Get human-readable error messages for user-facing applications

Exception Hierarchy:
    TikTikException (base)
    ├── CaptchaException     - TikTik showing captcha (bot detection)
    ├── NotFoundException    - Requested object doesn't exist
    ├── EmptyResponseException - Empty response (likely bot detection)
    ├── SoundRemovedException - Sound was removed by TikTik
    ├── InvalidJSONException - Response isn't valid JSON
    ├── InvalidResponseException - Response structure is unexpected
    └── (domain exceptions)  - See domain/exceptions.py for business errors
"""


class TikTikException(Exception):
    """
    Base exception for all TikTikApi errors.

    Attributes:
        raw_response: The raw response data that caused the error
        message: Human-readable error description
        error_code: Optional numeric error code from TikTik
    """

    def __init__(self, raw_response, message, error_code=None):
        self.error_code = error_code
        self.raw_response = raw_response
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.error_code} -> {self.message}"


class CaptchaException(TikTikException):
    """TikTik is showing a captcha - bot detection triggered."""


class NotFoundException(TikTikException):
    """The requested object (video, user, sound, etc.) does not exist."""


class EmptyResponseException(TikTikException):
    """
    TikTik returned an empty response.

    This usually means bot detection is active. Try:
    - headless=False (visible browser)
    - browser='webkit' (different browser engine)
    - Using a proxy
    - Providing valid ms_tokens
    """


class SoundRemovedException(TikTikException):
    """This sound was removed by TikTik and has no valid ID."""


class InvalidJSONException(TikTikException):
    """TikTik returned a response that is not valid JSON."""


class InvalidResponseException(TikTikException):
    """The response structure doesn't match what we expected."""
