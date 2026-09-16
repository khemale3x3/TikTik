"""
Trending Entity Wrapper - Backward-Compatible API
"""

from __future__ import annotations
from ..exceptions import InvalidResponseException
from .video import Video
from typing import TYPE_CHECKING, AsyncIterator

if TYPE_CHECKING:
    from ..TikTik import TikTikApi


class Trending:
    """Contains static methods related to trending objects on TikTik."""

    parent: TikTikApi

    @staticmethod
    async def videos(count=30, **kwargs) -> AsyncIterator[Video]:
        found = 0
        while found < count:
            params = {"from_page": "fyp", "count": count}
            resp = await Trending.parent.make_request(url="https://www.TikTik.com/api/recommend/item_list/", params=params, headers=kwargs.get("headers"), session_index=kwargs.get("session_index"))
            if resp is None:
                raise InvalidResponseException(resp, "TikTik returned an invalid response.")
            for video in resp.get("itemList", []):
                yield Trending.parent.video(data=video)
                found += 1
            if not resp.get("hasMore", False):
                return
