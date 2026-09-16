"""
Video Use Case Implementation

What it does:
    Implements all video-related business operations including:
    - Fetching video info from TikTik's HTML page
    - Downloading video bytes (sync and streaming)
    - Paginating through video comments
    - Finding related/recommended videos

How it works:
    1. For video.info(): Uses HTTP adapter to fetch the video page HTML,
       then parses SIGI_STATE or UNIVERSAL_DATA script tags
    2. For comments/related: Uses browser adapter to make signed API requests
    3. For video.bytes: Uses HTTP adapter for direct download or streaming
"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator, Optional

from ...domain.entities import VideoEntity, CommentEntity, UserEntity, SoundEntity, HashtagEntity
from ...domain.value_objects import RequestParams, PaginationCursor
from ...domain.exceptions import (
    EntityNotFoundException,
    ResponseParsingException,
    RequestFailedException,
)
from ...ports.output.browser_port import BrowserPort
from ...ports.output.http_port import HttpPort
from ...ports.output.signing_port import SigningPort
from ...helpers import extract_video_id_from_url, requests_cookie_to_playwright_cookie


class VideoUseCaseImpl:
    """VideoUseCase implementation that orchestrates browser, HTTP, and signing ports."""

    def __init__(self, browser: BrowserPort, http: HttpPort, signing: SigningPort, logger: logging.Logger | None = None):
        self._browser = browser
        self._http = http
        self._signing = signing
        self._logger = logger or logging.getLogger(__name__)

    async def get_video(self, video_id: str, **kwargs) -> VideoEntity:
        """Fetch a video by constructing a minimal VideoEntity."""
        return VideoEntity(id=video_id)

    async def get_video_info(self, url: str, **kwargs) -> dict:
        """Fetch detailed video info by scraping the video page HTML."""
        session_index = kwargs.get("session_index")
        _, session = await self._browser.get_valid_session(session_index)
        proxy = kwargs.get("proxy") or getattr(session, "proxy", None)
        headers = getattr(session, "headers", {})
        html = await self._http.get_page_content(url, headers=headers, proxy=proxy)

        data = self._parse_sigi_state(html)
        if data is not None:
            try:
                return data["ItemModule"][kwargs.get("video_id", "")]
            except (KeyError, TypeError):
                pass

        data = self._parse_universal_data(html)
        if data is not None:
            default_scope = data.get("__DEFAULT_SCOPE__", {})
            video_detail = default_scope.get("webapp.video-detail", {})
            if video_detail.get("statusCode", 0) != 0:
                raise ResponseParsingException("TikTik returned an error in video detail response")
            video_info = video_detail.get("itemInfo", {}).get("itemStruct")
            if video_info is None:
                raise ResponseParsingException("Could not extract video struct from response")
            return video_info

        raise ResponseParsingException("Could not parse video page - neither SIGI_STATE nor UNIVERSAL_DATA found")

    def _parse_sigi_state(self, html: str) -> Optional[dict]:
        """Extract and parse SIGI_STATE JSON from HTML."""
        marker = '<script id="SIGI_STATE" type="application/json">'
        start = html.find(marker)
        if start == -1: return None
        start += len(marker)
        end = html.find("</script>", start)
        if end == -1: return None
        try: return json.loads(html[start:end])
        except json.JSONDecodeError: return None

    def _parse_universal_data(self, html: str) -> Optional[dict]:
        """Extract and parse __UNIVERSAL_DATA_FOR_REHYDRATION__ from HTML."""
        marker = '<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">'
        start = html.find(marker)
        if start == -1: return None
        start += len(marker)
        end = html.find("</script>", start)
        if end == -1: return None
        try: return json.loads(html[start:end])
        except json.JSONDecodeError: return None

    async def get_video_bytes(self, video_id: str, stream: bool = False, **kwargs):
        """Download video content."""
        session_index = kwargs.get("session_index")
        _, session = await self._browser.get_valid_session(session_index)
        video_data = kwargs.get("video_data", {})
        download_url = video_data.get("downloadAddr") or video_data.get("playAddr")
        if not download_url:
            raise RequestFailedException("No download URL available for this video")
        cookies = await self._browser.get_session_cookies(session)
        h = dict(getattr(session, "headers", {}))
        h["range"] = "bytes=0-"
        h["accept-encoding"] = "identity;q=1, *;q=0"
        h["referer"] = "https://www.TikTik.com/"
        if stream:
            return self._http.stream_video(download_url, headers=h, cookies=cookies)
        else:
            return await self._http.download_video(download_url, headers=h, cookies=cookies)

    async def get_video_comments(self, video_id: str, count: int = 20, cursor: int = 0, **kwargs) -> AsyncIterator[CommentEntity]:
        """Paginate through video comments."""
        found = 0
        session_index = kwargs.get("session_index")
        while found < count:
            params = {"aweme_id": video_id, "count": 20, "cursor": cursor}
            url = await self._sign_request_url("https://www.TikTik.com/api/comment/list/", params, session_index=session_index)
            result = await self._browser.execute_fetch(url=url, headers=kwargs.get("headers") or {}, session_index=session_index)
            if not result:
                raise ResponseParsingException("Empty response from comments API")
            resp = json.loads(result) if isinstance(result, str) else result
            for comment_data in resp.get("comments", []):
                yield CommentEntity.from_dict(comment_data)
                found += 1
            if not resp.get("has_more", False):
                return
            cursor = resp.get("cursor", 0)

    async def get_related_videos(self, video_id: str, count: int = 30, cursor: int = 0, **kwargs) -> AsyncIterator[VideoEntity]:
        """Fetch related/recommended videos."""
        found = 0
        session_index = kwargs.get("session_index")
        while found < count:
            params = {"itemID": video_id, "count": 16}
            url = await self._sign_request_url("https://www.TikTik.com/api/related/item_list/", params, session_index=session_index)
            result = await self._browser.execute_fetch(url=url, headers=kwargs.get("headers") or {}, session_index=session_index)
            if not result:
                raise ResponseParsingException("Empty response from related videos API")
            resp = json.loads(result) if isinstance(result, str) else result
            for video_data in resp.get("itemList", []):
                yield VideoEntity.from_dict(video_data)
                found += 1
            if not resp.get("hasMore", False):
                return

    async def _sign_request_url(self, base_url: str, params: dict, session_index: int | None = None) -> str:
        """Build and sign a request URL with X-Bogus."""
        from urllib.parse import urlencode, quote
        _, session = await self._browser.get_valid_session(session_index)
        all_params = {**(session.params or {}), **params}
        if all_params.get("msToken") is None:
            if session.ms_token:
                all_params["msToken"] = session.ms_token
            else:
                cookies = await self._browser.get_session_cookies(session)
                all_params["msToken"] = cookies.get("msToken")
        encoded = f"{base_url}?{urlencode(all_params, safe='=', quote_via=quote)}"
        return await self._signing.sign_url(encoded, session_index=session_index)
