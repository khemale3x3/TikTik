"""
Comment Entity Wrapper - Backward-Compatible API
"""

from __future__ import annotations
from typing import ClassVar, AsyncIterator, Optional, TYPE_CHECKING
from ..exceptions import InvalidResponseException

if TYPE_CHECKING:
    from ..TikTik import TikTikApi
    from .user import User


class Comment:
    """A TikTik Comment - Legacy Backward-Compatible Wrapper."""

    parent: ClassVar[TikTikApi]
    id: str
    author: ClassVar[User]
    text: str
    likes_count: int
    as_dict: dict

    def __init__(self, data: Optional[dict] = None):
        if data is not None:
            self.as_dict = data
            self.__extract_from_data()

    def __extract_from_data(self):
        data = self.as_dict
        self.id = self.as_dict["cid"]
        self.text = self.as_dict["text"]
        usr = self.as_dict["user"]
        self.author = self.parent.user(user_id=usr["uid"], username=usr["unique_id"], sec_uid=usr["sec_uid"])
        self.likes_count = self.as_dict["digg_count"]

    async def replies(self, count=20, cursor=0, **kwargs) -> AsyncIterator[Comment]:
        found = 0
        while found < count:
            params = {"count": 20, "cursor": cursor, "item_id": self.author.user_id, "comment_id": self.id}
            resp = await self.parent.make_request(url="https://www.TikTik.com/api/comment/list/reply/", params=params, headers=kwargs.get("headers"), session_index=kwargs.get("session_index"))
            if resp is None:
                raise InvalidResponseException(resp, "TikTik returned an invalid response.")
            for comment in resp.get("comments", []):
                yield self.parent.comment(data=comment)
                found += 1
            if not resp.get("has_more", False):
                return
            cursor = resp.get("cursor")

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"TikTikApi.comment(comment_id='{getattr(self, 'id', None)}', text='{getattr(self, 'text', None)}')"
