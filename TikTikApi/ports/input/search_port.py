"""
Search Use Case Port - Inbound Interface
"""

from __future__ import annotations

from typing import AsyncIterator, Protocol

from ...domain.entities import UserEntity, VideoEntity


class SearchUseCase(Protocol):
    """Protocol defining search-related use cases."""

    async def search_users(
        self, query: str, count: int = 10, cursor: int = 0, **kwargs
    ) -> AsyncIterator[UserEntity]: ...
    async def search_videos(
        self, query: str, count: int = 10, cursor: int = 0, **kwargs
    ) -> AsyncIterator[VideoEntity]: ...
