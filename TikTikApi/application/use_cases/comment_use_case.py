"""Comment Use Case Implementation."""

from __future__ import annotations
import json
import logging
from typing import AsyncIterator
from ...domain.entities import CommentEntity
from ...domain.exceptions import ResponseParsingException
from ...ports.output.browser_port import BrowserPort
from ...ports.output.signing_port import SigningPort


class CommentUseCaseImpl:
    """CommentUseCase implementation."""

    def __init__(self, browser: BrowserPort, signing: SigningPort, logger: logging.Logger | None = None):
        self._browser = browser
        self._signing = signing
        self._logger = logger or logging.getLogger(__name__)

    async def get_comment_replies(self, comment_id: str, author_user_id: str, count: int = 20, cursor: int = 0, **kwargs) -> AsyncIterator[CommentEntity]:
        found = 0
        session_index = kwargs.get("session_index")
        while found < count:
            params = {"count": 20, "cursor": cursor, "item_id": author_user_id, "comment_id": comment_id}
            resp = await self._make_request("https://www.TikTik.com/api/comment/list/reply/", params, session_index=session_index)
            if resp is None:
                raise ResponseParsingException("Empty response from comment replies API")
            for comment_data in resp.get("comments", []):
                yield CommentEntity.from_dict(comment_data)
                found += 1
            if not resp.get("has_more", False):
                return
            cursor = resp.get("cursor", 0)

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
