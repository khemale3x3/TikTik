"""
Playlist Entity Wrapper - Backward-Compatible API
"""

from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar, AsyncIterator, Optional
from ..exceptions import InvalidResponseException

if TYPE_CHECKING:
    from ..TikTik import TikTikApi
    from .video import Video
    from .user import User


class Playlist:
    """A TikTik video playlist - Legacy Backward-Compatible Wrapper."""

    parent: ClassVar[TikTikApi]
    id: Optional[str]
    name: Optional[str]
    video_count: Optional[int]
    creator: Optional[User]
    cover_url: Optional[str]
    as_dict: dict

    def __init__(self, id: Optional[str] = None, data: Optional[dict] = None):
        if id is None and data is not None and data.get("id") is None:
            raise TypeError("You must provide id parameter.")
        self.id = id
        if data is not None:
            self.as_dict = data
            self.__extract_from_data()

    async def info(self, **kwargs) -> dict:
        id = getattr(self, "id", None)
        if not id:
            raise TypeError("You must provide the playlist id when creating this class to use this method.")
        url_params = {"mixId": id, "msToken": kwargs.get("ms_token")}
        resp = await self.parent.make_request(url="https://www.TikTik.com/api/mix/detail/", params=url_params, headers=kwargs.get("headers"), session_index=kwargs.get("session_index"))
        if resp is None:
            raise InvalidResponseException(resp, "TikTik returned an invalid response.")
        self.as_dict = resp["mixInfo"]
        self.__extract_from_data()
        return resp

    async def videos(self, count=30, cursor=0, **kwargs) -> AsyncIterator[Video]:
        id = getattr(self, "id", None)
        if id is None or id == "":
            await self.info(**kwargs)
        found = 0
        while found < count:
            params = {"mixId": id, "count": min(count, 30), "cursor": cursor}
            resp = await self.parent.make_request(url="https://www.TikTik.com/api/mix/item_list/", params=params, headers=kwargs.get("headers"), session_index=kwargs.get("session_index"))
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
        if "mixInfo" in keys:
            data = data["mixInfo"]
        self.id = data.get("id", None) or data.get("mixId", None)
        self.name = data.get("name", None) or data.get("mixName", None)
        self.video_count = data.get("videoCount", None)
        self.creator = self.parent.user(data=data.get("creator", {}))
        self.cover_url = data.get("cover", None)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"TikTikApi.playlist(id='{getattr(self, 'id', None)}')"
