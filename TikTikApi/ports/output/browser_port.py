"""
Browser Port - Outbound Interface for Browser Automation

What it does:
    Defines the contract for browser session management. The application
    layer uses this to create, manage, and destroy browser sessions without
    knowing whether it's using Playwright, Selenium, or another tool.

Why:
    The core challenge of scraping TikTik is bot detection. The browser port
    abstracts this entirely - the application layer just asks for "a valid
    session" and the adapter handles all the anti-detection complexity.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol

from ...domain.value_objects import SessionConfig


class BrowserPort(Protocol):
    """Protocol for browser session management."""

    async def create_sessions(
        self,
        num_sessions: int,
        config: SessionConfig,
        ms_tokens: Optional[list[str]] = None,
        proxies: Optional[list[dict[str, Any]]] = None,
        **kwargs,
    ) -> None: ...

    async def get_valid_session(self, session_index: Optional[int] = None) -> tuple[int, Any]: ...

    async def execute_fetch(
        self,
        url: str,
        headers: dict[str, str],
        session_index: Optional[int] = None,
    ) -> str: ...

    async def validate_session(self, session: Any) -> bool: ...
    async def invalidate_session(self, session: Any) -> None: ...
    async def close_all(self) -> None: ...
    async def get_session_cookies(self, session: Any) -> dict[str, str]: ...
    async def set_session_cookies(self, session: Any, cookies: list[dict]) -> None: ...
    def get_resource_stats(self) -> dict: ...
    async def health_check(self) -> dict: ...
