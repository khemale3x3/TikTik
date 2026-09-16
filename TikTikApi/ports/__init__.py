"""
Ports Layer - Hexagonal Architecture Contracts

Ports define the interfaces through which the application layer interacts
with the outside world. They are the "plugs" of the hexagon.
"""

from .input import (
    VideoUseCase,
    UserUseCase,
    SoundUseCase,
    HashtagUseCase,
    CommentUseCase,
    TrendingUseCase,
    SearchUseCase,
    PlaylistUseCase,
)
from .output import (
    BrowserPort,
    HttpPort,
    SigningPort,
)

__all__ = [
    "VideoUseCase",
    "UserUseCase",
    "SoundUseCase",
    "HashtagUseCase",
    "CommentUseCase",
    "TrendingUseCase",
    "SearchUseCase",
    "PlaylistUseCase",
    "BrowserPort",
    "HttpPort",
    "SigningPort",
]
