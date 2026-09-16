"""
User Use Case Implementation

What it does:
    Implements all user-related business operations:
    - Fetching user profile details
    - Paginating through user's posted videos, liked videos, and playlists
"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator, Optional

from ...domain.entities import UserEntity, VideoEntity, PlaylistEntity
from ...domain.exceptions import ResponseParsingException, EntityNotFoundException
from ...ports.output.browser_port import BrowserPort
from ...ports.output.signing_port import SigningPort


class UserUseCaseImpl:
    """UserUseCase implementation that orchestrates browser and signing ports."""

    def __init__(self, browser: BrowserPort, signing: SigningPort, logger: logging.Logger | None = None):
        self._browser = browser
        self._signing = signing
        self._logger = logger or logging.getLogger(__name__)

    async def get_user(self, username: str, **kwargs) -> UserEntity:
        """Fetch a user's full profile."""
        sec_uid = kwargs.get("sec_uid", "")
        session_index = kwargs.get("session_index")
        params = {"secUid": sec_uid or "", "uniqueId": username, "msToken": kwargs.get("ms_token")}
        resp = await self._make_request("https://www.TikTik.com/api/user/detail/", params, session_index=session_index)
        if resp is None:
            raise ResponseParsingException("Empty response from user detail API")
        return UserEntity.from_dict(resp)

    async def get_user_videos(self, username: str, count: int = 30, cursor: int = 0, **kwargs) -> AsyncIterator[VideoEntity]:
        """Paginate through a user's posted videos."""
        sec_uid = kwargs.get("sec_uid")
        if not sec_uid:
            user = await self.get_user(username, **kwargs)
            sec_uid = user.sec_uid
        found = 0
        session_index = kwargs.get("session_index")
        while found < count:
            params = {"secUid": sec_uid, "count": 30, "cursor": cursor}
            resp = await self._make_request("https://www.TikTik.com/api/post/item_list/", params, session_index=session_index)
            if resp is None:
                raise ResponseParsingException("Empty response from user videos API")
            for video_data in resp.get("itemList", []):
                yield VideoEntity.from_dict(video_data)
                found += 1
            if not resp.get("hasMore", False):
                return
            cursor = resp.get("cursor", 0)

    async def get_user_liked(self, username: str, count: int = 30, cursor: int = 0, **kwargs) -> AsyncIterator[VideoEntity]:
        """Paginate through a user's liked videos (if public)."""
        sec_uid = kwargs.get("sec_uid")
        if not sec_uid:
            user = await self.get_user(username, **kwargs)
            sec_uid = user.sec_uid
        found = 0
        session_index = kwargs.get("session_index")
        while found < count:
            params = {"secUid": sec_uid, "count": 30, "cursor": cursor}
            resp = await self._make_request("https://www.TikTik.com/api/favorite/item_list", params, session_index=session_index)
            if resp is None:
                raise ResponseParsingException("Empty response from user liked API")
            for video_data in resp.get("itemList", []):
                yield VideoEntity.from_dict(video_data)
                found += 1
            if not resp.get("hasMore", False):
                return
            cursor = resp.get("cursor", 0)

    async def get_user_playlists(self, username: str, count: int = 20, cursor: int = 0, **kwargs) -> AsyncIterator[PlaylistEntity]:
        """Paginate through a user's playlists."""
        sec_uid = kwargs.get("sec_uid")
        if not sec_uid:
            user = await self.get_user(username, **kwargs)
            sec_uid = user.sec_uid
        found = 0
        session_index = kwargs.get("session_index")
        while found < count:
            params = {"secUid": sec_uid, "count": min(count, 30), "cursor": cursor}
            resp = await self._make_request("https://www.TikTik.com/api/user/playlist", params, session_index=session_index)
            if resp is None:
                raise ResponseParsingException("Empty response from user playlists API")
            for playlist_data in resp.get("playList", []):
                yield PlaylistEntity.from_dict(playlist_data)
                found += 1
            if not resp.get("hasMore", False):
                return
            cursor = resp.get("cursor", 0)

    async def _make_request(self, url: str, params: dict, session_index: int | None = None):
        """Build, sign, and execute a request."""
        from urllib.parse import urlencode, quote
        _, session = await self._browser.get_valid_session(session_index)
        all_params = {**(session.params or {}), **params}
        if all_params.get("msToken") is None:
            if session.ms_token:
                all_params["msToken"] = session.ms_token
            else:
                cookies = await self._browser.get_session_cookies(session)
                all_params["msToken"] = cookies.get("msToken")
        encoded = f"{url}?{urlencode(all_params, safe='=', quote_via=quote)}"
        signed_url = await self._signing.sign_url(encoded, session_index=session_index)
        result = await self._browser.execute_fetch(url=signed_url, headers=session.headers or {}, session_index=session_index)
        if not result: return None
        return json.loads(result) if isinstance(result, str) else result
