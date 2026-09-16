"""
HTTP Adapter - Output Port Implementation

What it does:
    Implements the HttpPort protocol using `requests` for synchronous HTTP
    and `httpx` for async streaming. This adapter handles all direct HTTP
    communication with TikTik's servers.

How it works:
    - get_page_content(): Uses requests.get() to fetch HTML pages (for video.info())
    - stream_video(): Uses httpx async streaming for large video downloads
    - download_video(): Uses requests.get() for complete video downloads
    - resolve_redirect(): Uses requests.head() to follow URL redirects

Why:
    The application layer needs HTTP for two purposes:
    1. Fetching video page HTML (to extract video data from script tags)
    2. Downloading video content (bytes)

    These are different from the Playwright-based API requests because they
    don't need the anti-bot signing. By abstracting HTTP behind this port,
    we could switch to a unified async client or add caching transparently.
"""

from __future__ import annotations

from typing import AsyncIterator, Optional

import httpx
import requests


class HttpAdapter:
    """
    HttpPort implementation using requests + httpx.

    Handles synchronous page scraping and async video streaming.
    """

    async def get_page_content(
        self, url: str, headers: Optional[dict[str, str]] = None, proxy: Optional[str] = None,
    ) -> str:
        """Fetch a page's HTML content synchronously."""
        r = requests.get(url, headers=headers, proxies=proxy)
        r.raise_for_status()
        return r.text

    async def stream_video(
        self, url: str, headers: dict[str, str], cookies: dict[str, str],
    ) -> AsyncIterator[bytes]:
        """Stream video bytes asynchronously using httpx."""
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url, headers=headers, cookies=cookies) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk

    async def download_video(
        self, url: str, headers: dict[str, str], cookies: dict[str, str],
    ) -> bytes:
        """Download complete video content synchronously."""
        resp = requests.get(url, headers=headers, cookies=cookies)
        resp.raise_for_status()
        return resp.content

    async def resolve_redirect(self, url: str) -> str:
        """Follow redirects and return the final URL."""
        r = requests.head(url, allow_redirects=True)
        r.raise_for_status()
        return r.url
