"""
TikTikApi - An Unofficial TikTik API Wrapper (Hexagonal Architecture)

What it does:
    Provides a Python library for fetching publicly available data from TikTik
    using browser automation to bypass bot detection. Supports fetching videos,
    users, sounds, hashtags, comments, trending content, search results, and
    playlists.

How it works:
    Uses Playwright (headless browser) to execute JavaScript in a real browser
    context, generating the X-Bogus signatures required by TikTik's anti-bot
    system. All requests go through signed browser sessions.

    Architecture follows the Hexagonal (Ports & Adapters) pattern:
    - Domain: Pure entities (Video, User, Sound, etc.) with no dependencies
    - Ports: Interface contracts for input (use cases) and output (adapters)
    - Adapters: Playwright, HTTP, and Signing implementations
    - Application: Use cases that orchestrate ports to fulfill operations

Why:
    TikTik actively blocks automated access. This library bypasses detection
    by running requests inside real browser contexts. The hexagonal architecture
    makes the codebase testable, maintainable, and adaptable to changes in
    TikTik's anti-bot measures.

Usage:
    .. code-block:: python

        from TikTikApi import TikTikApi

        async with TikTikApi() as api:
            await api.create_sessions(num_sessions=5, ms_tokens=['token1'])

            # Get video info
            video = api.video(id='7041997751718137094')

            # Iterate user's videos
            async for v in api.user(username='therock').videos():
                print(v.id)

            # Get trending
            async for t in api.trending.videos():
                print(t.id)

Architecture Documentation:
    See ARCHITECTURE.md for detailed architecture documentation.
"""

from .TikTik import TikTikApi, TikTikPlaywrightSession

# Re-export domain entities for advanced usage
from .domain.entities import (
    VideoEntity,
    UserEntity,
    SoundEntity,
    HashtagEntity,
    CommentEntity,
    PlaylistEntity,
)

# Re-export adapters for dependency injection
from .adapters.composition_root import CompositionRoot
from .adapters.playwright_browser import PlaywrightBrowserAdapter
from .adapters.http_adapter import HttpAdapter
from .adapters.signing_adapter import SigningAdapter

# Re-export domain value objects
from .domain.value_objects import SessionConfig, RequestParams, PaginationCursor

__all__ = [
    # Main API
    "TikTikApi",
    "TikTikPlaywrightSession",
    # Domain Entities
    "VideoEntity",
    "UserEntity",
    "SoundEntity",
    "HashtagEntity",
    "CommentEntity",
    "PlaylistEntity",
    # Value Objects
    "SessionConfig",
    "RequestParams",
    "PaginationCursor",
    # Architecture Components
    "CompositionRoot",
    "PlaywrightBrowserAdapter",
    "HttpAdapter",
    "SigningAdapter",
]

__version__ = "8.0.0"
