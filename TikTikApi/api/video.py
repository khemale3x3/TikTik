"""
Video Entity Wrapper - Backward-Compatible API

What it does:
    Provides a backward-compatible Video class that wraps the new domain
    entities while maintaining the original API surface.

Why:
    Existing code using api.video(id='...') continues to work unchanged.
"""

from __future__ import annotations
from ..helpers import extract_video_id_from_url, requests_cookie_to_playwright_cookie
from typing import TYPE_CHECKING, ClassVar, AsyncIterator, Optional
from datetime import datetime
import requests
from ..exceptions import InvalidResponseException
import json
import httpx
from typing import Union

if TYPE_CHECKING:
    from ..TikTik import TikTikApi
    from .user import User
    from .sound import Sound
    from .hashtag import Hashtag
    from .comment import Comment


class Video:
    """
    A TikTik Video - Legacy Backward-Compatible Wrapper.

    Provides methods to fetch video data, comments, related videos,
    and download video content. Delegates to the parent TikTikApi instance.

    Usage:
        .. code-block:: python

            video = api.video(id='7041997751718137094')
            info = await video.info()
            async for comment in video.comments():
                print(comment.text)
    """

    parent: ClassVar[TikTikApi]

    id: Optional[str]
    url: Optional[str]
    create_time: Optional[datetime]
    stats: Optional[dict]
    author: Optional[User]
    sound: Optional[Sound]
    hashtags: Optional[list[Hashtag]]
    as_dict: dict

    def __init__(self, id: Optional[str] = None, url: Optional[str] = None, data: Optional[dict] = None, **kwargs):
        self.id = id
        self.url = url
        if data is not None:
            self.as_dict = data
            self.__extract_from_data()
        elif url is not None:
            i, session = self.parent._get_session(**kwargs)
            self.id = extract_video_id_from_url(
                url, headers=session.headers,
                proxy=(kwargs.get("proxy") if kwargs.get("proxy") is not None else session.proxy),
            )
        if getattr(self, "id", None) is None:
            raise TypeError("You must provide id or url parameter.")

    async def info(self, **kwargs) -> dict:
        """Returns a dictionary of all data associated with this video."""
        i, session = self.parent._get_session(**kwargs)
        proxy = kwargs.get("proxy") if kwargs.get("proxy") is not None else session.proxy
        if self.url is None:
            raise TypeError("To call video.info() you need to set the video's url.")
        r = requests.get(self.url, headers=session.headers, proxies=proxy)
        if r.status_code != 200:
            raise InvalidResponseException(r.text, "TikTik returned an invalid response.", error_code=r.status_code)
        start = r.text.find('<script id="SIGI_STATE" type="application/json">')
        if start != -1:
            start += len('<script id="SIGI_STATE" type="application/json">')
            end = r.text.find("</script>", start)
            if end == -1:
                raise InvalidResponseException(r.text, "TikTik returned an invalid response.", error_code=r.status_code)
            data = json.loads(r.text[start:end])
            video_info = data["ItemModule"][self.id]
        else:
            start = r.text.find('<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">')
            if start == -1:
                raise InvalidResponseException(r.text, "TikTik returned an invalid response.", error_code=r.status_code)
            start += len('<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">')
            end = r.text.find("</script>", start)
            if end == -1:
                raise InvalidResponseException(r.text, "TikTik returned an invalid response.", error_code=r.status_code)
            data = json.loads(r.text[start:end])
            default_scope = data.get("__DEFAULT_SCOPE__", {})
            video_detail = default_scope.get("webapp.video-detail", {})
            if video_detail.get("statusCode", 0) != 0:
                raise InvalidResponseException(r.text, "TikTik returned an invalid response structure.", error_code=r.status_code)
            video_info = video_detail.get("itemInfo", {}).get("itemStruct")
            if video_info is None:
                raise InvalidResponseException(r.text, "TikTik returned an invalid response structure.", error_code=r.status_code)
        self.as_dict = video_info
        self.__extract_from_data()
        cookies = [requests_cookie_to_playwright_cookie(c) for c in r.cookies]
        await self.parent.set_session_cookies(session, cookies)
        return video_info

    async def bytes(self, stream: bool = False, **kwargs) -> Union[bytes, AsyncIterator[bytes]]:
        """Returns the bytes of a TikTik Video."""
        i, session = self.parent._get_session(**kwargs)
        video_data = self.as_dict.get("video", {})
        downloadAddr = video_data.get("downloadAddr") or video_data.get("playAddr")
        cookies = await self.parent.get_session_cookies(session)
        h = session.headers
        h["range"] = "bytes=0-"
        h["accept-encoding"] = "identity;q=1, *;q=0"
        h["referer"] = "https://www.TikTik.com/"
        if stream:
            async def stream_bytes():
                async with httpx.AsyncClient() as client:
                    async with client.stream("GET", downloadAddr, headers=h, cookies=cookies) as response:
                        async for chunk in response.aiter_bytes():
                            yield chunk
            return stream_bytes()
        else:
            resp = requests.get(downloadAddr, headers=h, cookies=cookies)
            return resp.content

    def __extract_from_data(self) -> None:
        data = self.as_dict
        self.id = data["id"]
        timestamp = data.get("createTime", None)
        if timestamp is not None:
            try:
                timestamp = int(timestamp)
            except ValueError:
                pass
        self.create_time = datetime.fromtimestamp(timestamp)
        self.stats = data.get("statsV2") or data.get("stats")
        author = data.get("author")
        if isinstance(author, str):
            self.author = self.parent.user(username=author)
        else:
            self.author = self.parent.user(data=author)
        self.sound = self.parent.sound(data=data)
        self.hashtags = [self.parent.hashtag(data=hashtag) for hashtag in data.get("challenges", [])]

    async def comments(self, count=20, cursor=0, **kwargs) -> AsyncIterator[Comment]:
        found = 0
        while found < count:
            params = {"aweme_id": self.id, "count": 20, "cursor": cursor}
            resp = await self.parent.make_request(
                url="https://www.TikTik.com/api/comment/list/",
                params=params, headers=kwargs.get("headers"), session_index=kwargs.get("session_index"),
            )
            if resp is None:
                raise InvalidResponseException(resp, "TikTik returned an invalid response.")
            for video in resp.get("comments", []):
                yield self.parent.comment(data=video)
                found += 1
            if not resp.get("has_more", False):
                return
            cursor = resp.get("cursor")

    async def related_videos(self, count: int = 30, cursor: int = 0, **kwargs) -> AsyncIterator[Video]:
        found = 0
        while found < count:
            params = {"itemID": self.id, "count": 16}
            resp = await self.parent.make_request(
                url="https://www.TikTik.com/api/related/item_list/",
                params=params, headers=kwargs.get("headers"), session_index=kwargs.get("session_index"),
            )
            if resp is None:
                raise InvalidResponseException(resp, "TikTik returned an invalid response.")
            for video in resp.get("itemList", []):
                yield self.parent.video(data=video)
                found += 1

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"TikTikApi.video(id='{getattr(self, 'id', None)}')"
