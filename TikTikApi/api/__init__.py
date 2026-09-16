"""
API Layer - Legacy Entity Wrappers

What it does:
    Contains backward-compatible entity wrapper classes that maintain the
    original API surface while delegating to the hexagonal architecture.

    These wrappers are thin adapters between the old API style (where
    entities have a `parent` ClassVar pointing to the main TikTikApi)
    and the new hexagonal architecture where entities are standalone.

    The wrappers delegate all operations to the parent TikTikApi instance,
    which internally uses the hexagonal architecture's use cases and adapters.

How it works:
    Each wrapper class:
    1. Accepts an `id` or `data` dict during construction
    2. Stores a ClassVar `parent` reference to TikTikApi
    3. Delegates methods like .info(), .videos(), etc. to parent.make_request()

Why:
    Maintains 100% backward compatibility. Existing code like:
        video = api.video(id='123')
        async for v in api.user(username='therock').videos():
            ...

    ...continues to work unchanged while the internals are modernized.

Architecture Position:
    This layer sits between the Facade (TikTikApi) and the Application Layer.
    It translates the old "entity-as-object" pattern to the new "use case"
    pattern internally.
"""

from .video import Video
from .user import User
from .sound import Sound
from .hashtag import Hashtag
from .comment import Comment
from .trending import Trending
from .search import Search
from .playlist import Playlist

__all__ = [
    "Video",
    "User",
    "Sound",
    "Hashtag",
    "Comment",
    "Trending",
    "Search",
    "Playlist",
]
