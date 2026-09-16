"""
TikTikApi - Hexagonal Architecture Facade

What it does:
    The TikTikApi class is the main entry point for the library. It acts as
    a Facade, providing a simple, unified API while internally delegating to
    the hexagonal architecture (domain, ports, adapters, application layers).

How it works:
    1. On initialization, creates a CompositionRoot that wires all adapters
    2. Exposes domain entities (Video, User, Sound, etc.) as class-level accessors
    3. Delegates all operations to use case implementations
    4. Maintains backward compatibility with the original API surface

Why:
    The facade pattern allows us to:
    - Refactor internals without breaking existing code
    - Gradually migrate users to the new hexagonal API
    - Keep the "simple" API for quick use while enabling advanced patterns
    - Maintain the same import path: from TikTikApi import TikTikApi

Architecture:
    Consumer -> Facade -> Use Cases (Application) -> Ports -> Adapters -> External Systems
         ^                        |
         |                        v
         +--- Domain Entities (Video, User, Sound, etc.)
"""

from __future__ import annotations

import asyncio
import logging
import dataclasses
from typing import Any, Optional

from playwright.async_api import (
    Browser,
    Playwright,
    ProxySettings,
)
from proxyproviders import ProxyProvider
from proxyproviders.algorithms import Algorithm

from .adapters.composition_root import CompositionRoot
from .adapters.playwright_browser import PlaywrightBrowserAdapter
from .domain.value_objects import SessionConfig

# Re-export backward-compatible entity wrappers
from .api.video import Video
from .api.user import User
from .api.sound import Sound
from .api.hashtag import Hashtag
from .api.comment import Comment
from .api.trending import Trending
from .api.search import Search
from .api.playlist import Playlist


@dataclasses.dataclass
class TikTikPlaywrightSession:
    """
    Backward-compatible session wrapper.

    Wraps the internal PlaywrightBrowserSession for backward compatibility
    with code that accesses session properties directly.
    """

    context: Any
    page: Any
    proxy: str = None
    params: dict = None
    headers: dict = None
    ms_token: str = None
    base_url: str = "https://www.TikTik.com"
    is_valid: bool = True


class TikTikApi:
    """
    The main TikTikApi class - Facade over the Hexagonal Architecture.

    Provides a simple, familiar API while internally using clean architecture:

        Consumer
            |
            v
        TikTikApi (Facade)
            |
            +-> CompositionRoot (DI Container)
            |       |
            |       +-> PlaywrightBrowserAdapter (BrowserPort)
            |       +-> HttpAdapter (HttpPort)
            |       +-> SigningAdapter (SigningPort)
            |
            +-> Use Cases (Application Layer)
            |       |
            |       +-> VideoUseCaseImpl
            |       +-> UserUseCaseImpl
            |       +-> SoundUseCaseImpl
            |       +-> HashtagUseCaseImpl
            |       +-> CommentUseCaseImpl
            |       +-> TrendingUseCaseImpl
            |       +-> SearchUseCaseImpl
            |       +-> PlaylistUseCaseImpl
            |
            +-> Domain Entities
                    |
                    +-> VideoEntity, UserEntity, SoundEntity, etc.

    Usage:
        .. code-block:: python

            from TikTikApi import TikTikApi

            async with TikTikApi() as api:
                await api.create_sessions(num_sessions=5, ms_tokens=['token1'])

                # Access entities (backward-compatible)
                video = api.video(id='7041997751718137094')
                async for v in api.user(username='therock').videos():
                    print(v.id)

    Advanced Usage (Direct Hexagonal Access):
        .. code-block:: python

            from TikTikApi import TikTikApi

            api = TikTikApi()
            await api.create_sessions(...)

            # Access the composition root for advanced use
            root = api._root
            video_entity = await root.video.get_video("some_id")

            # Or swap adapters
            from TikTikApi.adapters import HttpAdapter
            root.http = MyCustomHttpAdapter()
    """

    # Entity class accessors (backward-compatible)
    user = User
    video = Video
    sound = Sound
    hashtag = Hashtag
    comment = Comment
    trending = Trending
    search = Search
    playlist = Playlist

    def __init__(self, logging_level: int = logging.WARN, logger_name: str = None):
        """
        Create a TikTikApi instance.

        Args:
            logging_level: Python logging level (e.g., logging.DEBUG, logging.INFO)
            logger_name: Custom logger name (defaults to module name)
        """
        # Setup logger
        if logger_name is None:
            logger_name = __name__
        self._setup_logger(logger_name, logging_level)

        # Create the hexagonal architecture composition root
        self._root = CompositionRoot.create(logger=self.logger)

        # Expose the browser adapter for backward compatibility
        self._browser_adapter: PlaywrightBrowserAdapter = self._root.browser

        # Backward-compatible session access
        self.sessions: list = []

        # Proxy provider (backward compatibility)
        self._proxy_provider: Optional[ProxyProvider] = None
        self._proxy_algorithm: Optional[Algorithm] = None

        # Wire entity parent references (backward compatibility)
        User.parent = self
        Video.parent = self
        Sound.parent = self
        Hashtag.parent = self
        Comment.parent = self
        Trending.parent = self
        Search.parent = self
        Playlist.parent = self

    def _setup_logger(self, name: str, level: int = logging.DEBUG):
        """Configure the logger."""
        self.logger: logging.Logger = logging.getLogger(name)
        self.logger.setLevel(level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    # --- Session Lifecycle (Delegates to Browser Adapter) ---

    async def create_sessions(
        self,
        num_sessions: int = 5,
        headless: bool = True,
        ms_tokens: list[str] | None = None,
        proxies: list[dict[str, Any] | ProxySettings] | None = None,
        proxy_provider: Optional[ProxyProvider] = None,
        proxy_algorithm: Optional[Algorithm] = None,
        sleep_after: int = 1,
        starting_url: str = "https://www.TikTik.com",
        context_options: dict[str, Any] = {},
        override_browser_args: list[str] | None = None,
        cookies: list[dict[str, Any]] | None = None,
        suppress_resource_load_types: list[str] | None = None,
        browser: str = "chromium",
        executable_path: str | None = None,
        page_factory=None,
        browser_context_factory=None,
        timeout: int = 30000,
        enable_session_recovery: bool = True,
        allow_partial_sessions: bool = False,
        min_sessions: int | None = None,
    ):
        """
        Create browser sessions for making requests to TikTik.

        This delegates to the PlaywrightBrowserAdapter via the CompositionRoot.

        Args:
            num_sessions: Number of browser sessions to create
            headless: Run browser in headless mode
            ms_tokens: Pre-obtained msToken values for anti-bot protection
            proxies: List of proxy configurations
            proxy_provider: Smart proxy rotation provider
            proxy_algorithm: Algorithm for proxy selection
            sleep_after: Seconds to wait after session creation for token generation
            starting_url: Initial URL to navigate to
            context_options: Additional Playwright context options
            override_browser_args: Custom browser launch arguments
            cookies: Initial cookies to set
            suppress_resource_load_types: Browser resource types to block
            browser: Browser type ('chromium', 'firefox', 'webkit')
            executable_path: Path to browser executable
            page_factory: Custom page creation function
            browser_context_factory: Custom context creation function
            timeout: Page navigation timeout in milliseconds
            enable_session_recovery: Auto-recover dead sessions
            allow_partial_sessions: Succeed even if some sessions fail
            min_sessions: Minimum sessions required (when allow_partial=True)
        """
        self._proxy_provider = proxy_provider
        self._proxy_algorithm = proxy_algorithm

        if proxies is not None and proxy_provider is not None:
            raise ValueError(
                "Cannot use both 'proxies' and 'proxy_provider'. Use 'proxy_provider' (recommended)."
            )

        config = SessionConfig(
            starting_url=starting_url,
            sleep_after_creation=sleep_after,
            timeout_ms=timeout,
            suppress_resource_load_types=tuple(suppress_resource_load_types or []),
            cookies=_merge_cookies_dict(cookies),
            headless=headless,
            browser_type=browser,
        )

        await self._browser_adapter.create_sessions(
            num_sessions=num_sessions,
            config=config,
            ms_tokens=ms_tokens,
            proxies=proxies,
            context_options=context_options,
            suppress_resource_load_types=suppress_resource_load_types,
            executable_path=executable_path,
            override_browser_args=override_browser_args,
            page_factory=page_factory,
            browser_context_factory=browser_context_factory,
            allow_partial_sessions=allow_partial_sessions,
            min_sessions=min_sessions,
            enable_session_recovery=enable_session_recovery,
        )

        # Update backward-compatible sessions list
        self._sync_sessions()

    def _sync_sessions(self):
        """Sync internal sessions list with browser adapter."""
        self.sessions = self._browser_adapter.sessions

    async def close_sessions(self):
        """Close all sessions and clean up browser resources."""
        await self._browser_adapter.close_all()
        self.sessions.clear()
        self._cleanup_called = True

    async def stop_playwright(self):
        """Stop the Playwright browser (included in close_sessions)."""
        await self._browser_adapter.close_all()

    # --- Request Methods (Delegates to Signing + Browser Adapters) ---

    async def make_request(
        self,
        url: str,
        headers: dict = None,
        params: dict = None,
        retries: int = 3,
        exponential_backoff: bool = True,
        **kwargs,
    ):
        """
        Make a signed request to TikTik's API.

        Builds the URL, signs it with X-Bogus, and executes it via the browser.

        Args:
            url: The API endpoint URL
            headers: Custom HTTP headers
            params: Query parameters
            retries: Number of retry attempts
            exponential_backoff: Use exponential backoff between retries

        Returns:
            dict: The parsed JSON response
        """
        import json
        from urllib.parse import urlencode, quote

        session_index = kwargs.get("session_index")

        i, session = await self._get_valid_session_index(**kwargs)

        if session.params is not None:
            params = {**session.params, **(params or {})}
        else:
            params = params or {}

        if headers is not None:
            headers = {**(session.headers or {}), **headers}
        else:
            headers = session.headers

        # Get msToken
        if params.get("msToken") is None:
            if session.ms_token is not None:
                params["msToken"] = session.ms_token
            else:
                cookies = await self.get_session_cookies(session)
                ms_token = cookies.get("msToken")
                if ms_token is None:
                    self.logger.warn(
                        "Failed to get msToken from cookies, request may fail"
                    )
                params["msToken"] = ms_token

        encoded_params = f"{url}?{urlencode(params, safe='=', quote_via=quote)}"
        signed_url = await self.sign_url(encoded_params, session_index=i)

        retry_count = 0
        while retry_count < retries:
            retry_count += 1
            try:
                result = await self.run_fetch_script(
                    signed_url, headers=headers, session_index=i
                )

                if result is None:
                    raise Exception("run_fetch_script returned None")

                if result == "":
                    from .exceptions import EmptyResponseException
                    raise EmptyResponseException(
                        result,
                        "TikTik returned empty response. Try: headless=False, browser='webkit', or use a proxy.",
                    )

                try:
                    data = json.loads(result)
                    if data.get("status_code") != 0:
                        self.logger.error(f"Unexpected status code: {data}")
                    return data
                except json.decoder.JSONDecodeError:
                    if retry_count == retries:
                        from .exceptions import InvalidJSONException
                        self.logger.error(f"Failed to decode JSON: {result}")
                        raise InvalidJSONException()

                    self.logger.info(f"Retry {retry_count}/{retries}")
                    if exponential_backoff:
                        await asyncio.sleep(2**retry_count)
                    else:
                        await asyncio.sleep(1)

            except Exception as e:
                from playwright.async_api import Error as PlaywrightError
                if isinstance(e, PlaywrightError):
                    self.logger.error(f"Playwright error: {e}")
                    await self._mark_session_invalid(session)
                    if retry_count < retries:
                        try:
                            i, session = await self._get_valid_session_index(**kwargs)
                        except Exception:
                            raise
                    else:
                        raise
                else:
                    raise

    async def run_fetch_script(self, url: str, headers: dict, **kwargs):
        """Execute a JavaScript fetch in the browser."""
        _, session = await self._get_valid_session_index(**kwargs)
        js_script = self._generate_js_fetch("GET", url, headers)

        try:
            return await session.page.evaluate(js_script)
        except Exception as e:
            self.logger.error(f"Session failed during fetch: {e}")
            await self._mark_session_invalid(session)
            raise

    def _generate_js_fetch(self, method: str, url: str, headers: dict) -> str:
        """Generate JavaScript fetch function."""
        import json
        headers_js = json.dumps(headers)
        return f"""
            () => {{
                return new Promise((resolve, reject) => {{
                    fetch('{url}', {{ method: '{method}', headers: {headers_js} }})
                        .then(response => response.text())
                        .then(data => resolve(data))
                        .catch(error => reject(error.message));
                }});
            }}
        """

    async def sign_url(self, url: str, **kwargs):
        """Sign a URL with X-Bogus."""
        i, session = await self._get_valid_session_index(**kwargs)
        x_bogus = (await self.generate_x_bogus(url, session_index=i)).get("X-Bogus")
        if x_bogus is None:
            raise Exception("Failed to generate X-Bogus")
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}X-Bogus={x_bogus}"

    async def generate_x_bogus(self, url: str, **kwargs):
        """Generate X-Bogus for a URL."""
        _, session = await self._get_valid_session_index(**kwargs)

        import random
        from playwright.async_api import TimeoutError, Error as PlaywrightError

        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                timeout_time = random.randint(5000, 20000)
                await session.page.wait_for_function(
                    "window.byted_acrawler !== undefined", timeout=timeout_time
                )
                break
            except TimeoutError:
                if attempt == max_attempts - 1:
                    raise TimeoutError(
                        f"Failed to load TikTik after {max_attempts} attempts"
                    )
                try_urls = [
                    "https://www.TikTik.com/foryou",
                    "https://www.TikTik.com",
                    "https://www.TikTik.com/@TikTik",
                ]
                await session.page.goto(random.choice(try_urls))
            except PlaywrightError as e:
                self.logger.error(f"Session died during x-bogus: {e}")
                await self._mark_session_invalid(session)
                raise

        try:
            return await session.page.evaluate(
                f'() => {{ return window.byted_acrawler.frontierSign("{url}") }}'
            )
        except PlaywrightError as e:
            self.logger.error(f"Session died during x-bogus eval: {e}")
            await self._mark_session_invalid(session)
            raise

    # --- Session Management (Backward Compatibility) ---

    async def _get_valid_session_index(self, **kwargs):
        """Get a valid session with recovery."""
        session_index = kwargs.get("session_index")
        max_attempts = 3

        for attempt in range(max_attempts):
            if session_index is not None:
                if session_index < len(self.sessions):
                    session = self.sessions[session_index]
                    if await self._is_session_valid(session):
                        return session_index, session
            else:
                valid = []
                for idx, session in enumerate(self.sessions):
                    if await self._is_session_valid(session):
                        valid.append((idx, session))
                if valid:
                    import random
                    return random.choice(valid)

            if attempt < max_attempts - 1:
                self.logger.warning(f"Recovery attempt {attempt + 1}/{max_attempts}")
                await self._recover_sessions()
            else:
                break

        raise Exception("No valid sessions available.")

    def _get_session(self, **kwargs):
        """Get a random session (backward compatibility)."""
        import random
        if not self.sessions:
            raise Exception("No sessions created")
        i = kwargs.get("session_index") or random.randint(0, len(self.sessions) - 1)
        return i, self.sessions[i]

    async def _is_session_valid(self, session) -> bool:
        """Check if a session is valid."""
        if not getattr(session, "is_valid", True):
            return False
        try:
            _ = session.page.url
            return True
        except Exception:
            session.is_valid = False
            return False

    async def _mark_session_invalid(self, session):
        """Mark a session as invalid."""
        session.is_valid = False
        try:
            if session.page:
                await session.page.close()
        except Exception:
            pass
        try:
            if session.context:
                await session.context.close()
        except Exception:
            pass
        if session in self.sessions:
            try:
                self.sessions.remove(session)
            except ValueError:
                pass

    async def _recover_sessions(self):
        """Clean up dead sessions."""
        self.sessions = [s for s in self.sessions if await self._is_session_valid(s)]

    async def set_session_cookies(self, session, cookies):
        """Set cookies on a session."""
        await session.context.add_cookies(cookies)

    async def get_session_cookies(self, session):
        """Get cookies from a session."""
        cookies = await session.context.cookies()
        return {c["name"]: c["value"] for c in cookies}

    async def get_session_content(self, url: str, **kwargs):
        """Get the content of a URL via a session."""
        _, session = await self._get_valid_session_index(**kwargs)
        try:
            return await session.page.content()
        except Exception as e:
            self.logger.error(f"Session died during get_session_content: {e}")
            await self._mark_session_invalid(session)
            raise

    # --- Health & Stats (Delegates to Browser Adapter) ---

    def get_resource_stats(self) -> dict:
        """Get current resource usage statistics."""
        return self._browser_adapter.get_resource_stats()

    async def health_check(self) -> dict:
        """Perform a health check on all sessions."""
        return await self._browser_adapter.health_check()

    # --- Cleanup ---

    def __del__(self):
        """Destructor safety net."""
        if not getattr(self, "_cleanup_called", False):
            if self.sessions:
                self.logger.warning(
                    "TikTikApi destroyed without cleanup. Use 'async with TikTikApi()' or call close_sessions()."
                )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close_sessions()


def _merge_cookies_dict(cookies_list) -> dict:
    """Merge a list of cookie dicts into a single dict."""
    if not cookies_list:
        return {}
    merged = {}
    for cookie_dict in cookies_list:
        if cookie_dict:
            merged.update(cookie_dict)
    return merged
