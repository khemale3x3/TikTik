"""
Sound Entity Wrapper - Backward-Compatible API
"""

from __future__ import annotations
from ..exceptions import *
from typing import TYPE_CHECKING, ClassVar, AsyncIterator, Optional

if TYPE_CHECKING:
    from ..TikTik import TikTikApi
    from .user import User
    from .video import Video


class Sound:
    """A TikTik Sound/Music/Song - Legacy Backward-Compatible Wrapper."""

    parent: ClassVar[TikTikApi]
    id: str
    title: Optional[str]
    author: Optional[User]
    duration: Optional[int]
    original: Optional[bool]

    def __init__(self, id: Optional[str] = None, data: Optional[str] = None):
        if data is not None:
            self.as_dict = data
            self.__extract_from_data()
        elif id is None:
            raise TypeError("You must provide id parameter.")
        else:
            self.id = id

    async def info(self, **kwargs) -> dict:
        id = getattr(self, "id", None)
        if not id:
            raise TypeError("You must provide the id when creating this class to use this method.")
        url_params = {"msToken": kwargs.get("ms_token"), "musicId": id}
        resp = await self.parent.make_request(url="https://www.TikTik.com/api/music/detail/", params=url_params, headers=kwargs.get("headers"), session_index=kwargs.get("session_index"))
        if resp is None:
            raise InvalidResponseException(resp, "TikTik returned an invalid response.")
        self.as_dict = resp
        self.__extract_from_data()
        return resp

    async def videos(self, count=30, cursor=0, **kwargs) -> AsyncIterator[Video]:
        id = getattr(self, "id", None)
        if id is None:
            raise TypeError("You must provide the id when creating this class to use this method.")
        found = 0
        while found < count:
            params = {"musicID": id, "count": 30, "cursor": cursor}
            resp = await self.parent.make_request(url="https://www.TikTik.com/api/music/item_list/", params=params, headers=kwargs.get("headers"), session_index=kwargs.get("session_index"))
            if resp is None:
                raise InvalidResponseException(resp, "TikTik returned an invalid response.")
            for video in resp.get("itemList", []):
                yield self.parent.video(data=video)
                found += 1
            if not resp.get("hasMore", False):
                return
            cursor = resp.get("cursor")

    def __extract_from_data(self):
        data = self.as_dict
        keys = data.keys()
        if "musicInfo" in keys:
            author = data.get("musicInfo").get("author")
            if isinstance(author, dict):
                self.author = self.parent.user(data=author)
            elif isinstance(author, str):
                self.author = self.parent.user(username=author)
            if data.get("musicInfo").get("music"):
                self.title = data.get("musicInfo").get("music").get("title")
                self.id = data.get("musicInfo").get("music").get("id")
                self.original = data.get("musicInfo").get("music").get("original")
                self.play_url = data.get("musicInfo").get("music").get("playUrl")
                self.cover_large = data.get("musicInfo").get("music").get("coverLarge")
                self.duration = data.get("musicInfo").get("music").get("duration")
        if "music" in keys:
            self.title = data.get("music").get("title")
            self.id = data.get("music").get("id")
            self.original = data.get("music").get("original")
            self.play_url = data.get("music").get("playUrl")
            self.cover_large = data.get("music").get("coverLarge")
            self.duration = data.get("music").get("duration")
        if "stats" in keys:
            self.stats = data.get("stats")

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"TikTikApi.sound(id='{getattr(self, 'id', None)}')"
