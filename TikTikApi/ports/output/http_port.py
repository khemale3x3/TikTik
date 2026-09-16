"""
HTTP Port - Outbound Interface for HTTP Operations

What it does:
    Defines the contract for making HTTP requests to TikTik's servers.
    This covers both synchronous requests (for HTML page scraping) and
    asynchronous streaming (for video downloads).
"""

from __future__ import annotations

from typing import AsyncIterator, Optional, Protocol


class HttpPort(Protocol):
    """Protocol for HTTP communication with TikTik servers."""

    async def get_page_content(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        proxy: Optional[str] = None,
    ) -> str: ...

    async def stream_video(
        self,
        url: str,
        headers: dict[str, str],
        cookies: dict[str, str],
    ) -> AsyncIterator[bytes]: ...

    async def download_video(
        self,
        url: str,
        headers: dict[str, str],
        cookies: dict[str, str],
    ) -> bytes: ...

    async def resolve_redirect(self, url: str) -> str: ...
