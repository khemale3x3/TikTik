"""
Domain Value Objects - Immutable Composite Data

What it does:
    Defines immutable value objects that represent complex parameters and
    return types used throughout the domain. Unlike entities, value objects
    have no identity - they are compared by their attributes.

How it works:
    Each value object is a frozen dataclass that:
    1. Groups related parameters into a single typed object
    2. Enforces invariants at construction time
    3. Provides clear documentation of what data is expected/returned

Why:
    Value objects reduce parameter lists, prevent argument order mistakes,
    and make the code self-documenting. They also serve as contracts between
    the application layer and adapters - when an adapter receives a
    RequestParams object, it knows exactly what fields are available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class SessionConfig:
    """
    Immutable configuration for a browser session.

    This is used by the application layer to configure adapters without
    the adapters needing to know about the full API context.

    Attributes:
        starting_url: The URL to navigate to when creating a session
        sleep_after_creation: Seconds to wait after page load for tokens
        timeout_ms: Page navigation timeout in milliseconds
        suppress_resource_types: Browser resource types to block (e.g., 'image')
        cookies: Initial cookies to set on the session
        headless: Whether to run the browser in headless mode
        browser_type: Browser engine ('chromium', 'firefox', 'webkit')
    """

    starting_url: str = "https://www.TikTik.com"
    sleep_after_creation: int = 1
    timeout_ms: int = 30000
    suppress_resource_types: tuple[str, ...] = ()
    cookies: dict[str, str] = field(default_factory=dict)
    headless: bool = True
    browser_type: str = "chromium"


@dataclass(frozen=True)
class RequestParams:
    """
    Immutable parameters for a TikTik API request.

    Represents all data needed to make a single request to TikTik's internal
    API. This object is constructed by use cases and consumed by adapters.

    Attributes:
        url: The full TikTik API endpoint URL
        params: Query parameters to include in the request
        headers: HTTP headers to include
        ms_token: The anti-bot session token (optional)
        session_index: Specific session to use (optional, random if None)
        retries: Number of retry attempts on failure
        exponential_backoff: Whether to use exponential backoff between retries
    """

    url: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    headers: Optional[dict[str, str]] = None
    ms_token: Optional[str] = None
    session_index: Optional[int] = None
    retries: int = 3
    exponential_backoff: bool = True


@dataclass(frozen=True)
class PaginationCursor:
    """
    Immutable pagination state for TikTik's cursor-based pagination.

    TikTik uses cursor-based pagination (not page numbers). This value object
    encapsulates the cursor state and makes pagination logic explicit.

    Attributes:
        count: Maximum number of items to return
        cursor: The offset/cursor for the current page
        has_more: Whether more pages are available (set after first response)
    """

    count: int = 30
    cursor: int = 0
    has_more: bool = True

    def next_page(self, new_cursor: int) -> PaginationCursor:
        """Create a new cursor for the next page."""
        return PaginationCursor(count=self.count, cursor=new_cursor, has_more=True)

    def stop(self) -> PaginationCursor:
        """Create a stopped cursor (no more pages)."""
        return PaginationCursor(count=self.count, cursor=self.cursor, has_more=False)


@dataclass
class VideoInfo:
    """
    Mutable container for video information fetched from TikTik's HTML page.

    Unlike other value objects, this is mutable because video.info() may
    update it with data from either SIGI_STATE or UNIVERSAL_DATA format.

    Attributes:
        video_id: The extracted video ID
        raw_data: The complete parsed video data dictionary
        format_source: Which HTML format was used ('SIGI_STATE' or 'UNIVERSAL')
    """

    video_id: Optional[str] = None
    raw_data: Optional[dict] = None
    format_source: Optional[str] = None
