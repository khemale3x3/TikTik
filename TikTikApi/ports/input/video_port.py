"""
Video Use Case Port - Inbound Interface

What it does:
    Defines the contract for all video-related operations that the
    application exposes to consumers.
"""

from __future__ import annotations

from typing import AsyncIterator, Protocol

from ...domain.entities import VideoEntity, CommentEntity


class VideoUseCase(Protocol):
    """Protocol defining video-related use cases."""

    async def get_video(self, video_id: str, **kwargs) -> VideoEntity: ...
    async def get_video_info(self, url: str, **kwargs) -> dict: ...
    async def get_video_bytes(self, video_id: str, stream: bool = False, **kwargs): ...
    async def get_video_comments(
        self, video_id: str, count: int = 20, cursor: int = 0, **kwargs
    ) -> AsyncIterator[CommentEntity]: ...
    async def get_related_videos(
        self, video_id: str, count: int = 30, cursor: int = 0, **kwargs
    ) -> AsyncIterator[VideoEntity]: ...
