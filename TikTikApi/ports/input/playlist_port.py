"""
Playlist Use Case Port - Inbound Interface
"""

from __future__ import annotations

from typing import AsyncIterator, Protocol

from ...domain.entities import PlaylistEntity, VideoEntity


class PlaylistUseCase(Protocol):
    """Protocol defining playlist-related use cases."""

    async def get_playlist(self, playlist_id: str, **kwargs) -> PlaylistEntity: ...
    async def get_playlist_videos(
        self, playlist_id: str, count: int = 30, cursor: int = 0, **kwargs
    ) -> AsyncIterator[VideoEntity]: ...
