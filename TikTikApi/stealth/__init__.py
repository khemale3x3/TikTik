"""
Stealth Module - Anti-Detection JavaScript Injection

What it does:
    Provides JavaScript scripts that are injected into Playwright pages to
    make them appear as regular user browsers rather than automated tools.

How it works:
    The stealth_async() function applies init scripts to a Playwright page.
    These scripts modify browser APIs (navigator, WebGL, Chrome objects)
    to remove headless browser fingerprints.

Why:
    TikTik uses browser fingerprinting to detect automated access. Without
    stealth scripts, Playwright-generated pages would be immediately
    identified as bots and blocked.
"""

from .stealth import stealth_async, StealthConfig

__all__ = ["stealth_async", "StealthConfig"]
