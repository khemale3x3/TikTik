"""
User Entity Wrapper - Backward-Compatible API
"""

from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar, AsyncIterator, Optional
from ..exceptions import InvalidResponseException

if TYPE_CHECKING:
    from ..TikTik import TikTikApi
    from .video import Video
    from .playlist import Playlist


class User:
    """A TikTik User - Legacy Backward-Compatible Wrapper."""

    parent: ClassVar[TikTikApi]
    user_id: str
    sec_uid: str
    username: str
    as_dict: dict

    def __init__(self, username: Optional[str] = None, user_id: Optional[str] = None, sec_uid: Optional[str] = None, data: Optional[dict] = None):
        self.__update_id_sec_uid_username(user_id, sec_uid, username)
        if data is not None:
            self.as_dict = data
            self.__extract_from_data()

    async def info(self, **kwargs) -> dict:
        username = getattr(self, "username", None)
        if not username:
            raise TypeError("You must provide the username when creating this class to use this method.")
        sec_uid = getattr(self, "sec_uid", None)
        url_params = {"secUid": sec_uid if sec_uid is not None else "", "uniqueId": username, "msToken": kwargs.get("ms_token")}
        resp = await self.parent.make_request(url="https://www.TikTik.com/api/user/detail/", params=url_params, headers=kwargs.get("headers"), session_index=kwargs.get("session_index"))
        if resp is None:
            raise InvalidResponseException(resp, "TikTik returned an invalid response.")
        self.as_dict = resp
        self.__extract_from_data()
        return resp

    async def playlists(self, count=20, cursor=0, **kwargs) -> AsyncIterator[Playlist]:
        sec_uid = getattr(self, "sec_uid", None)
        if sec_uid is None or sec_uid == "":
            await self.info(**kwargs)
        found = 0
        while found < count:
            params = {"secUid": self.sec_uid, "count": min(count, 30), "cursor": cursor}
            resp = await self.parent.make_request(url="https://www.TikTik.com/api/user/playlist", params=params, headers=kwargs.get("headers"), session_index=kwargs.get("session_index"))
            if resp is None:
                raise InvalidResponseException(resp, "TikTik returned an invalid response.")
            for playlist in resp.get("playList", []):
                yield self.parent.playlist(data=playlist)
                found += 1
            if not resp.get("hasMore", False):
                return
            cursor = resp.get("cursor")

    async def videos(self, count=30, cursor=0, **kwargs) -> AsyncIterator[Video]:
        sec_uid = getattr(self, "sec_uid", None)
        if sec_uid is None or sec_uid == "":
            await self.info(**kwargs)
        found = 0
        while found < count:
            params = {"secUid": self.sec_uid, "count": 30, "cursor": cursor}
            resp = await self.parent.make_request(url="https://www.TikTik.com/api/post/item_list/", params=params, headers=kwargs.get("headers"), session_index=kwargs.get("session_index"))
            if resp is None:
                raise InvalidResponseException(resp, "TikTik returned an invalid response.")
            for video in resp.get("itemList", []):
                yield self.parent.video(data=video)
                found += 1
            if not resp.get("hasMore", False):
                return
            cursor = resp.get("cursor")

    async def liked(self, count: int = 30, cursor: int = 0, **kwargs) -> AsyncIterator[Video]:
        sec_uid = getattr(self, "sec_uid", None)
        if sec_uid is None or sec_uid == "":
            await self.info(**kwargs)
        found = 0
        while found < count:
            params = {"secUid": self.sec_uid, "count": 30, "cursor": cursor}
            resp = await self.parent.make_request(url="https://www.TikTik.com/api/favorite/item_list", params=params, headers=kwargs.get("headers"), session_index=kwargs.get("session_index"))
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
        if "userInfo" in keys:
            self.__update_id_sec_uid_username(data["userInfo"]["user"]["id"], data["userInfo"]["user"]["secUid"], data["userInfo"]["user"]["uniqueId"])
        else:
            self.__update_id_sec_uid_username(data["id"], data["secUid"], data["uniqueId"])

    def __update_id_sec_uid_username(self, id, sec_uid, username):
        self.user_id = id
        self.sec_uid = sec_uid
        self.username = username

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"TikTikApi.user(username='{getattr(self, 'username', None)}', user_id='{getattr(self, 'user_id', None)}', sec_uid='{getattr(self, 'sec_uid', None)}')"
