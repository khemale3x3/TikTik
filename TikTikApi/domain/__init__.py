"""
Domain Layer - Hexagonal Architecture Core

The domain layer contains the core business logic and entities of the TikTikApi.
It has ZERO external dependencies - no imports from adapters, ports, or infrastructure.

What it does:
    Defines the core domain entities (Video, User, Sound, etc.) and value objects
    that represent the business concepts of the TikTik API.

How it works:
    Each entity is a pure Python dataclass with methods that encapsulate business rules.
    Entities are created from raw data and validate/transform it during construction.

Why:
    By keeping the domain layer pure, we ensure business logic is testable, portable,
    and independent of infrastructure concerns like HTTP clients or browser automation.
    This follows the Dependency Inversion Principle - high-level modules (domain) don't
    depend on low-level modules (adapters); both depend on abstractions (ports).
"""

from .entities import (
    VideoEntity,
    UserEntity,
    SoundEntity,
    HashtagEntity,
    CommentEntity,
    PlaylistEntity,
)
from .value_objects import (
    SessionConfig,
    RequestParams,
    PaginationCursor,
    VideoInfo,
)

__all__ = [
    "VideoEntity",
    "UserEntity",
    "SoundEntity",
    "HashtagEntity",
    "CommentEntity",
    "PlaylistEntity",
    "SessionConfig",
    "RequestParams",
    "PaginationCursor",
    "VideoInfo",
]
