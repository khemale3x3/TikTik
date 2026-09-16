"""
Search Entity Wrapper - Backward-Compatible API
"""

from __future__ import annotations
from urllib.parse import urlencode
from typing import TYPE_CHECKING, AsyncIterator
from .user import User
from ..exceptions import InvalidResponseException

if TYPE_CHECKING:
    from ..TikTik import TikTikApi


class Search:
    """Contains static methods about searching TikTik for a phrase."""

    parent: TikTikApi

    @staticmethod
    async def users(search_term, count=10, cursor=0, **kwargs) -> AsyncIterator[User]:
        async for user in Search.search_type(search_term, "user", count=count, cursor=cursor, **kwargs):
            yield user

    @staticmethod
    async def search_type(search_term, obj_type, count=10, cursor=0, **kwargs) -> AsyncIterator:
        found = 0
        search_id = ""
        while found < count:
            params = {"keyword": search_term, "cursor": cursor, "from_page": "search",
                      "web_search_code": '{"TikTik":{"client_params_x":{"search_engine":{"ies_mt_user_live_video_card_use_libra":1,"mt_search_general_user_live_card":1}},"search_server":{}}}'}
            if search_id != "":
                params["search_id"] = search_id
            resp = await Search.parent.make_request(url=f"https://www.TikTik.com/api/search/{obj_type}/full/", params=params, headers=kwargs.get("headers"), session_index=kwargs.get("session_index"))
            if resp is None:
                raise InvalidResponseException(resp, "TikTik returned an invalid response.")
            if obj_type == "user":
                for user in resp.get("user_list", []):
                    sec_uid = user.get("user_info").get("sec_uid")
                    uid = user.get("user_info").get("user_id")
                    username = user.get("user_info").get("unique_id")
                    yield Search.parent.user(sec_uid=sec_uid, user_id=uid, username=username)
                    found += 1
            elif obj_type == "item":
                for video in resp.get("item_list", []):
                    yield Search.parent.video(data=video)
                    found += 1
            if not resp.get("has_more", False):
                return
            cursor = resp.get("cursor")
            search_id = resp.get("rid", "")
