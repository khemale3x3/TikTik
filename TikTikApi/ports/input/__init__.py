"""
Input Ports - Use Cases the Application Provides

What it does:
    Defines the interfaces for all high-level use cases that consumers
    of the API can invoke.
"""

from .video_port import VideoUseCase
from .user_port import UserUseCase
from .sound_port import SoundUseCase
from .hashtag_port import HashtagUseCase
from .comment_port import CommentUseCase
from .trending_port import TrendingUseCase
from .search_port import SearchUseCase
from .playlist_port import PlaylistUseCase

__all__ = [
    "VideoUseCase",
    "UserUseCase",
    "SoundUseCase",
    "HashtagUseCase",
    "CommentUseCase",
    "TrendingUseCase",
    "SearchUseCase",
    "PlaylistUseCase",
]
