"""Search Use Case Implementation."""

from __future__ import annotations
import json
import logging
from typing import AsyncIterator
from ...domain.entities import UserEntity, VideoEntity
from ...domain.exceptions import ResponseParsingException
from ...ports.output.browser_port import BrowserPort
from ...ports.output.signing_port import SigningPort


class SearchUseCaseImpl:
    """SearchUseCase implementation."""

    def __init__(self, browser: BrowserPort, signing: SigningPort, logger: logging.Logger | None = None):
        self._browser = browser
        self._signing = signing
        self._logger = logger or logging.getLogger(__name__)

    async def search_users(self, query: str, count: int = 10, cursor: int = 0, **kwargs) -> AsyncIterator[UserEntity]:
        async for user in self._search_type(query, "user", count=count, cursor=cursor, **kwargs):
            yield user

    async def search_videos(self, query: str, count: int = 10, cursor: int = 0, **kwargs) -> AsyncIterator[VideoEntity]:
        async for video in self._search_type(query, "item", count=count, cursor=cursor, **kwargs):
            yield video

    async def _search_type(self, query: str, obj_type: str, count: int = 10, cursor: int = 0, **kwargs) -> AsyncIterator:
        found = 0
        search_id = ""
        session_index = kwargs.get("session_index")
        while found < count:
            params = {"keyword": query, "cursor": cursor, "from_page": "search",
                      "web_search_code": '{"TikTik":{"client_params_x":{"search_engine":{"ies_mt_user_live_video_card_use_libra":1,"mt_search_general_user_live_card":1}},"search_server":{}}}'}
            if search_id: params["search_id"] = search_id
            resp = await self._make_request(f"https://www.TikTik.com/api/search/{obj_type}/full/", params, session_index=session_index)
            if resp is None:
                raise ResponseParsingException("Empty response from search API")
            if obj_type == "user":
                for user_data in resp.get("user_list", []):
                    info = user_data.get("user_info", {})
                    yield UserEntity(user_id=info.get("user_id"), sec_uid=info.get("sec_uid"), username=info.get("unique_id"))
                    found += 1
            elif obj_type == "item":
                for video_data in resp.get("item_list", []):
                    yield VideoEntity.from_dict(video_data)
                    found += 1
            if not resp.get("has_more", False):
                return
            cursor = resp.get("cursor", 0)
            search_id = resp.get("rid", "")

    async def _make_request(self, url: str, params: dict, session_index: int | None = None):
        from urllib.parse import urlencode, quote
        _, session = await self._browser.get_valid_session(session_index)
        all_params = {**(session.params or {}), **params}
        if all_params.get("msToken") is None:
            if session.ms_token: all_params["msToken"] = session.ms_token
            else:
                cookies = await self._browser.get_session_cookies(session)
                all_params["msToken"] = cookies.get("msToken")
        encoded = f"{url}?{urlencode(all_params, safe='=', quote_via=quote)}"
        signed_url = await self._signing.sign_url(encoded, session_index=session_index)
        result = await self._browser.execute_fetch(url=signed_url, headers=session.headers or {}, session_index=session_index)
        if not result: return None
        return json.loads(result) if isinstance(result, str) else result
