"""
Domain Entities - Core Business Objects

What it does:
    Defines immutable(ish) domain entities that represent TikTik's core concepts:
    Video, User, Sound, Hashtag, Comment, and Playlist.

How it works:
    Each entity is a dataclass that:
    1. Accepts raw TikTik API response data during construction
    2. Extracts and validates relevant fields
    3. Provides typed access to domain data
    4. Maintains relationships between entities (e.g., Video -> User, Video -> Sound)

Why:
    Entities are the heart of the domain layer. They encapsulate business rules like
    "a Video must have an author (User)" and "a Sound belongs to a User". By placing
    them in the domain layer with no external dependencies, we ensure:
    - Business logic is always consistent regardless of how data arrives
    - Entities can be tested without mocking HTTP clients or browsers
    - The same entities work whether data comes from an API, cache, or database
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class UserEntity:
    """
    Represents a TikTik User.

    Attributes:
        user_id: TikTik's unique identifier for the user
        sec_uid: Security identifier used for API calls
        username: The user's public handle (e.g., '@therock')
        as_dict: Raw API response data for this user
    """

    user_id: Optional[str] = None
    sec_uid: Optional[str] = None
    username: Optional[str] = None
    as_dict: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "UserEntity":
        """Construct a UserEntity from a raw TikTik API response dict."""
        if "userInfo" in data:
            user_data = data["userInfo"]["user"]
            return cls(
                user_id=user_data.get("id"),
                sec_uid=user_data.get("secUid"),
                username=user_data.get("uniqueId"),
                as_dict=data,
            )
        return cls(
            user_id=data.get("id"),
            sec_uid=data.get("secUid"),
            username=data.get("uniqueId"),
            as_dict=data,
        )

    def has_valid_id(self) -> bool:
        """Check if this user has enough identifiers for API operations."""
        return all(v is not None for v in (self.user_id, self.sec_uid, self.username))


@dataclass
class VideoEntity:
    """
    Represents a TikTik Video.

    Attributes:
        id: TikTik's unique identifier for the video
        url: The video's URL on TikTik.com
        create_time: When the video was posted
        stats: View count, like count, comment count, share count, etc.
        author: The user who created the video
        sound: The sound/music used in the video
        hashtags: Hashtags in the video's caption
        as_dict: Raw API response data for this video
    """

    id: Optional[str] = None
    url: Optional[str] = None
    create_time: Optional[datetime] = None
    stats: Optional[dict] = None
    author: Optional[UserEntity] = None
    sound: Optional["SoundEntity"] = None
    hashtags: list["HashtagEntity"] = field(default_factory=list)
    as_dict: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "VideoEntity":
        """Construct a VideoEntity from a raw TikTik API response dict."""
        timestamp = data.get("createTime")
        if timestamp is not None:
            try:
                timestamp = datetime.fromtimestamp(int(timestamp))
            except (ValueError, TypeError, OSError):
                timestamp = None

        author_data = data.get("author")
        author = None
        if isinstance(author_data, str):
            author = UserEntity(username=author_data)
        elif isinstance(author_data, dict):
            author = UserEntity.from_dict(author_data)

        return cls(
            id=data.get("id"),
            create_time=timestamp,
            stats=data.get("statsV2") or data.get("stats"),
            author=author,
            sound=SoundEntity.from_video_data(data),
            hashtags=[HashtagEntity.from_dict(h) for h in data.get("challenges", [])],
            as_dict=data,
        )

    @property
    def download_url(self) -> Optional[str]:
        """Get the download URL for the video."""
        video_data = self.as_dict.get("video", {})
        return video_data.get("downloadAddr") or video_data.get("playAddr")

    @property
    def play_url(self) -> Optional[str]:
        """Get the play URL for the video."""
        video_data = self.as_dict.get("video", {})
        return video_data.get("playAddr")


@dataclass
class SoundEntity:
    """
    Represents a TikTik Sound/Music/Song.

    Attributes:
        id: TikTik's unique identifier for the sound
        title: The name of the song/sound
        author: The user who created/owns the sound
        duration: Duration in seconds
        original: Whether this is an original sound
        play_url: URL to play the sound
        cover_large: URL to the large cover image
        stats: Play count, like count, etc.
        as_dict: Raw API response data
    """

    id: Optional[str] = None
    title: Optional[str] = None
    author: Optional[UserEntity] = None
    duration: Optional[int] = None
    original: Optional[bool] = None
    play_url: Optional[str] = None
    cover_large: Optional[str] = None
    stats: Optional[dict] = None
    as_dict: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "SoundEntity":
        """Construct a SoundEntity from raw API data."""
        author_data = None
        if "musicInfo" in data:
            author_data = data["musicInfo"].get("author")
        elif "author" in data:
            author_data = data.get("author")

        author = None
        if isinstance(author_data, dict):
            author = UserEntity.from_dict(author_data)
        elif isinstance(author_data, str):
            author = UserEntity(username=author_data)

        music_data = data.get("musicInfo", {}).get("music") or data.get("music", {})

        return cls(
            id=music_data.get("id"),
            title=music_data.get("title"),
            author=author,
            duration=music_data.get("duration"),
            original=music_data.get("original"),
            play_url=music_data.get("playUrl"),
            cover_large=music_data.get("coverLarge"),
            stats=data.get("stats"),
            as_dict=data,
        )

    @classmethod
    def from_video_data(cls, data: dict) -> "SoundEntity":
        """Construct a SoundEntity from video-level data."""
        return cls(
            id=data.get("music", {}).get("id"),
            title=data.get("music", {}).get("title"),
            original=data.get("music", {}).get("original"),
            play_url=data.get("music", {}).get("playUrl"),
            cover_large=data.get("music", {}).get("coverLarge"),
            as_dict=data.get("music", {}),
        )


@dataclass
class HashtagEntity:
    """
    Represents a TikTik Hashtag/Challenge.

    Attributes:
        id: TikTik's unique identifier for the hashtag
        name: The hashtag text without the '#'
        split_name: Alternative display name
        stats: View count, video count, etc.
        as_dict: Raw API response data
    """

    id: Optional[str] = None
    name: Optional[str] = None
    split_name: Optional[str] = None
    stats: Optional[dict] = None
    as_dict: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "HashtagEntity":
        """Construct a HashtagEntity from raw API data."""
        if "title" in data:
            return cls(id=data.get("id"), name=data.get("title"), as_dict=data)

        challenge_info = data.get("challengeInfo", {})
        challenge = challenge_info.get("challenge", {})
        return cls(
            id=challenge.get("id"),
            name=challenge.get("title"),
            split_name=challenge.get("splitTitle"),
            stats=challenge_info.get("stats"),
            as_dict=data,
        )


@dataclass
class CommentEntity:
    """
    Represents a TikTik Comment.

    Attributes:
        id: The comment's unique identifier (cid)
        author: The user who wrote the comment
        text: The comment content
        likes_count: Number of likes on the comment
        as_dict: Raw API response data
    """

    id: Optional[str] = None
    author: Optional[UserEntity] = None
    text: Optional[str] = None
    likes_count: int = 0
    as_dict: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "CommentEntity":
        """Construct a CommentEntity from raw API data."""
        user_data = data.get("user", {})
        return cls(
            id=data.get("cid"),
            text=data.get("text"),
            author=UserEntity(
                user_id=user_data.get("uid"),
                username=user_data.get("unique_id"),
                sec_uid=user_data.get("sec_uid"),
            ),
            likes_count=data.get("digg_count", 0),
            as_dict=data,
        )


@dataclass
class PlaylistEntity:
    """
    Represents a TikTik Video Playlist.

    Attributes:
        id: TikTik's unique identifier for the playlist
        name: The playlist's display name
        video_count: Number of videos in the playlist
        creator: The user who created the playlist
        cover_url: URL to the playlist's cover image
        as_dict: Raw API response data
    """

    id: Optional[str] = None
    name: Optional[str] = None
    video_count: Optional[int] = None
    creator: Optional[UserEntity] = None
    cover_url: Optional[str] = None
    as_dict: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "PlaylistEntity":
        """Construct a PlaylistEntity from raw API data."""
        mix_info = data.get("mixInfo", data)
        creator_data = mix_info.get("creator", {})
        creator = None
        if creator_data:
            creator = UserEntity.from_dict(creator_data)

        return cls(
            id=mix_info.get("id") or mix_info.get("mixId"),
            name=mix_info.get("name") or mix_info.get("mixName"),
            video_count=mix_info.get("videoCount"),
            creator=creator,
            cover_url=mix_info.get("cover"),
            as_dict=data,
        )
