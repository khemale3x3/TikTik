"""
Sound Use Case Port - Inbound Interface
"""

from __future__ import annotations

from typing import AsyncIterator, Protocol

from ...domain.entities import SoundEntity, VideoEntity


class SoundUseCase(Protocol):
    """Protocol defining sound-related use cases."""

    async def get_sound(self, sound_id: str, **kwargs) -> SoundEntity: ...
    async def get_sound_videos(
        self, sound_id: str, count: int = 30, cursor: int = 0, **kwargs
    ) -> AsyncIterator[VideoEntity]: ...
