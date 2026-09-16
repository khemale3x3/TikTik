"""
User Use Case Port - Inbound Interface
"""

from __future__ import annotations

from typing import AsyncIterator, Protocol

from ...domain.entities import UserEntity, VideoEntity, PlaylistEntity


class UserUseCase(Protocol):
    """Protocol defining user-related use cases."""

    async def get_user(self, username: str, **kwargs) -> UserEntity: ...
    async def get_user_videos(
        self, username: str, count: int = 30, cursor: int = 0, **kwargs
    ) -> AsyncIterator[VideoEntity]: ...
    async def get_user_liked(
        self, username: str, count: int = 30, cursor: int = 0, **kwargs
    ) -> AsyncIterator[VideoEntity]: ...
    async def get_user_playlists(
        self, username: str, count: int = 20, cursor: int = 0, **kwargs
    ) -> AsyncIterator[PlaylistEntity]: ...
