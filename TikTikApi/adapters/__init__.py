"""
Adapters Layer - Concrete Implementations of Ports

What it does:
    Contains the concrete implementations of the port interfaces. Each adapter
    wraps a specific technology (Playwright, requests, httpx) and implements
    the corresponding port protocol.

How it works:
    Adapters are injected into the application layer at startup. They handle
    all the technical details (browser automation, HTTP, anti-detection) while
    the application layer focuses on business logic orchestration.

Why:
    This layer is where all the "dirty work" lives:
    - Playwright browser management and anti-detection stealth
    - HTTP request execution with proxy support
    - Request signing via browser JavaScript execution
    - Cookie management and session recovery

    By isolating these in adapters, the rest of the codebase stays clean
    and testable. You can swap any adapter without affecting domain or
    application logic.
"""

from .playwright_browser import PlaywrightBrowserAdapter
from .http_adapter import HttpAdapter
from .signing_adapter import SigningAdapter
from .composition_root import CompositionRoot

__all__ = [
    "PlaywrightBrowserAdapter",
    "HttpAdapter",
    "SigningAdapter",
    "CompositionRoot",
]
