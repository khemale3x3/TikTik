"""
Hashtag Use Case Port - Inbound Interface
"""

from __future__ import annotations

from typing import AsyncIterator, Protocol

from ...domain.entities import HashtagEntity, VideoEntity


class HashtagUseCase(Protocol):
    """Protocol defining hashtag-related use cases."""

    async def get_hashtag(self, name: str, **kwargs) -> HashtagEntity: ...
    async def get_hashtag_videos(
        self, name: str, count: int = 30, cursor: int = 0, **kwargs
    ) -> AsyncIterator[VideoEntity]: ...
