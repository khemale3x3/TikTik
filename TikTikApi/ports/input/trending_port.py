"""
Trending Use Case Port - Inbound Interface
"""

from __future__ import annotations

from typing import AsyncIterator, Protocol

from ...domain.entities import VideoEntity


class TrendingUseCase(Protocol):
    """Protocol defining trending-related use cases."""

    async def get_trending_videos(
        self, count: int = 30, **kwargs
    ) -> AsyncIterator[VideoEntity]: ...
