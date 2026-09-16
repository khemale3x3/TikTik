"""
Playwright Browser Adapter - Output Port Implementation

What it does:
    Implements the BrowserPort protocol using Playwright for browser automation.
    This adapter manages the complete lifecycle of browser sessions including:
    - Launching chromium/firefox/webkit browsers
    - Creating and managing browser contexts with proxies and cookies
    - Applying anti-detection stealth scripts
    - Executing JavaScript fetch requests within browser context
    - Session health monitoring and automatic recovery

How it works:
    1. create_sessions() launches N browser sessions concurrently
    2. Each session navigates to TikTik and captures request headers + msToken
    3. get_valid_session() picks a random healthy session from the pool
    4. execute_fetch() runs fetch() in the browser context to make API calls
    5. Sessions are automatically recovered on failure

Why:
    TikTik's bot detection requires requests to come from a real browser context.
    This adapter wraps all Playwright complexity behind a clean interface so that
    the application layer just calls "execute_fetch" without worrying about:
    - Which session to use
    - How to handle stale sessions
    - Anti-detection stealth injection
    - Cookie and token management
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from typing import Any, Awaitable, Callable, Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    ProxySettings,
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Error as PlaywrightError,
)

from ..domain.value_objects import SessionConfig
from ..stealth import stealth_async


class PlaywrightBrowserSession:
    """Internal representation of a Playwright browser session."""

    __slots__ = (
        "context", "page", "proxy", "params", "headers",
        "ms_token", "base_url", "is_valid",
    )

    def __init__(
        self,
        context: BrowserContext,
        page: Page,
        proxy: str | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        ms_token: str | None = None,
        base_url: str = "https://www.TikTik.com",
        is_valid: bool = True,
    ):
        self.context = context
        self.page = page
        self.proxy = proxy
        self.params = params
        self.headers = headers
        self.ms_token = ms_token
        self.base_url = base_url
        self.is_valid = is_valid


class PlaywrightBrowserAdapter:
    """
    BrowserPort implementation using Playwright.

    Manages a pool of browser sessions and provides methods for executing
    requests within those sessions.
    """

    def __init__(self, logger: logging.Logger | None = None):
        self._sessions: list[PlaywrightBrowserSession] = []
        self._browser: Browser | None = None
        self._playwright: Playwright | None = None
        self._session_creation_lock = asyncio.Lock()
        self._recovery_enabled = True
        self._auto_cleanup = True
        self._cleanup_called = False
        self._logger = logger or logging.getLogger(__name__)

    @property
    def sessions(self) -> list:
        return self._sessions

    # --- Session Lifecycle ---

    async def create_sessions(
        self,
        num_sessions: int,
        config: SessionConfig,
        ms_tokens: list[str] | None = None,
        proxies: list[dict[str, Any] | ProxySettings] | None = None,
        context_options: dict[str, Any] | None = None,
        suppress_resource_load_types: list[str] | None = None,
        executable_path: str | None = None,
        override_browser_args: list[str] | None = None,
        page_factory: Callable[[BrowserContext], Awaitable[Page]] | None = None,
        browser_context_factory: Callable[[Playwright], Awaitable[BrowserContext]] | None = None,
        allow_partial_sessions: bool = False,
        min_sessions: int | None = None,
        **kwargs,
    ) -> None:
        """Create browser sessions with anti-detection measures."""
        self._recovery_enabled = kwargs.get("enable_session_recovery", True)

        self._playwright = await async_playwright().start()

        if browser_context_factory is not None:
            self._browser = await browser_context_factory(self._playwright)
        elif config.browser_type == "chromium":
            headless = config.headless
            args = override_browser_args
            if headless and args is None:
                args = ["--headless=new"]
                headless = False
            self._browser = await self._playwright.chromium.launch(
                headless=headless, args=args, executable_path=executable_path,
            )
        elif config.browser_type == "firefox":
            self._browser = await self._playwright.firefox.launch(
                headless=config.headless, args=override_browser_args,
                executable_path=executable_path,
            )
        elif config.browser_type == "webkit":
            self._browser = await self._playwright.webkit.launch(
                headless=config.headless, args=override_browser_args,
                executable_path=executable_path,
            )
        else:
            raise ValueError(f"Invalid browser type: {config.browser_type}")

        if allow_partial_sessions:
            results = await asyncio.gather(
                *(
                    self._create_single_session(
                        config=config, ms_token=_random_choice(ms_tokens),
                        proxy=_random_choice(proxies),
                        suppress_resource_load_types=suppress_resource_load_types,
                        context_options=context_options or {}, timeout=config.timeout_ms,
                        page_factory=page_factory,
                    )
                    for _ in range(num_sessions)
                ),
                return_exceptions=True,
            )
            failed = sum(1 for r in results if isinstance(r, Exception))
            success = len(self._sessions)
            minimum = min_sessions if min_sessions is not None else 1
            if success < minimum:
                raise Exception(
                    f"Failed to create minimum sessions. Created {success}/{num_sessions}, needed at least {minimum}."
                )
            if failed > 0:
                self._logger.warning(f"Created {success}/{num_sessions} sessions. {failed} failed.")
        else:
            await asyncio.gather(
                *(
                    self._create_single_session(
                        config=config, ms_token=_random_choice(ms_tokens),
                        proxy=_random_choice(proxies),
                        suppress_resource_load_types=suppress_resource_load_types,
                        context_options=context_options or {}, timeout=config.timeout_ms,
                        page_factory=page_factory,
                    )
                    for _ in range(num_sessions)
                )
            )

    async def _create_single_session(
        self, config: SessionConfig, ms_token: str | None = None,
        proxy: dict | ProxySettings | None = None,
        suppress_resource_load_types: list[str] | None = None,
        context_options: dict[str, Any] | None = None,
        timeout: int = 30000, page_factory: Callable | None = None,
    ) -> None:
        """Create and initialize a single browser session."""
        try:
            cookies = dict(config.cookies)
            if ms_token is not None:
                cookies["msToken"] = ms_token

            if proxy is not None:
                context = await self._browser.new_context(proxy=proxy, **(context_options or {}))
            else:
                context = await self._browser.new_context(**(context_options or {}))

            if cookies:
                formatted_cookies = [
                    {"name": k, "value": v, "domain": "www.TikTik.com", "path": "/"}
                    for k, v in cookies.items() if v is not None
                ]
                await context.add_cookies(formatted_cookies)

            async def _apply_suppression(page: Page) -> None:
                if suppress_resource_load_types is None:
                    return
                await page.route(
                    "**/*",
                    lambda route, request: (
                        route.abort() if request.resource_type in suppress_resource_load_types
                        else route.continue_()
                    ),
                )

            if page_factory:
                page = await page_factory(context)
            else:
                page = await context.new_page()
                await stealth_async(page)
                await _apply_suppression(page)
                _ = await page.goto(config.starting_url)

            if "TikTik" not in page.url:
                _ = await page.goto("https://www.TikTik.com")

            request_headers = None
            def handle_request(request):
                nonlocal request_headers
                request_headers = request.headers
            page.once("request", handle_request)

            if page_factory:
                await _apply_suppression(page)

            page.set_default_navigation_timeout(timeout)

            x, y = random.randint(0, 50), random.randint(0, 50)
            a, b = random.randint(1, 50), random.randint(100, 200)
            await page.mouse.move(x, y)
            await page.wait_for_load_state("networkidle")
            await page.mouse.move(a, b)

            session = PlaywrightBrowserSession(
                context=context, page=page, ms_token=ms_token,
                proxy=proxy, headers=request_headers,
                base_url=config.starting_url,
            )

            if ms_token is None:
                await asyncio.sleep(config.sleep_after_creation)
                cookies_dict = await self.get_session_cookies(session)
                ms_token = cookies_dict.get("msToken")
                session.ms_token = ms_token

            self._sessions.append(session)
            await self._set_session_params(session)

        except Exception as e:
            self._logger.error(f"Failed to create session: {e}")
            if "page" in locals():
                try: await page.close()
                except Exception: pass
            if "context" in locals():
                try: await context.close()
                except Exception: pass
            raise

    async def _set_session_params(self, session: PlaywrightBrowserSession) -> None:
        """Extract and set session parameters from the browser context."""
        user_agent = await session.page.evaluate("() => navigator.userAgent")
        language = await session.page.evaluate("() => navigator.language || navigator.userLanguage")
        platform = await session.page.evaluate("() => navigator.platform")
        device_id = str(random.randint(10**18, 10**19 - 1))
        history_len = str(random.randint(1, 10))
        screen_height = str(random.randint(600, 1080))
        screen_width = str(random.randint(800, 1920))
        timezone = await session.page.evaluate("() => Intl.DateTimeFormat().resolvedOptions().timeZone")

        session.params = {
            "aid": "1988", "app_language": language, "app_name": "TikTik_web",
            "browser_language": language, "browser_name": "Mozilla",
            "browser_online": "true", "browser_platform": platform,
            "browser_version": user_agent, "channel": "TikTik_web",
            "cookie_enabled": "true", "device_id": device_id,
            "device_platform": "web_pc", "focus_state": "true",
            "from_page": "user", "history_len": history_len,
            "is_fullscreen": "false", "is_page_visible": "true",
            "language": language, "os": platform, "priority_region": "",
            "referer": "", "region": "US", "screen_height": screen_height,
            "screen_width": screen_width, "tz_name": timezone,
            "webcast_language": language,
        }

    # --- Session Management ---

    async def get_valid_session(self, session_index: int | None = None) -> tuple[int, PlaywrightBrowserSession]:
        """Get a valid session with automatic recovery."""
        max_attempts = 3
        for attempt in range(max_attempts):
            if session_index is not None:
                if session_index < len(self._sessions):
                    session = self._sessions[session_index]
                    if await self.validate_session(session):
                        return session_index, session
            else:
                valid = [(idx, s) for idx, s in enumerate(self._sessions) if await self.validate_session(s)]
                if valid:
                    return random.choice(valid)

            if self._recovery_enabled and attempt < max_attempts - 1:
                self._logger.warning(f"No valid sessions, recovery attempt {attempt + 1}/{max_attempts}")
                await self._recover_sessions()
            else:
                break

        raise Exception("No valid sessions available. Call create_sessions() again.")

    async def validate_session(self, session: PlaywrightBrowserSession) -> bool:
        """Check if a session's page is still alive."""
        if not session.is_valid:
            return False
        try:
            _ = session.page.url
            return True
        except (PlaywrightError, AttributeError):
            session.is_valid = False
            return False

    async def invalidate_session(self, session: PlaywrightBrowserSession) -> None:
        """Mark session as dead and clean up."""
        session.is_valid = False
        try:
            if session.page: await session.page.close()
        except Exception: pass
        try:
            if session.context: await session.context.close()
        except Exception: pass
        if self._auto_cleanup and session in self._sessions:
            try: self._sessions.remove(session)
            except ValueError: pass

    async def _recover_sessions(self) -> None:
        """Clean up dead sessions from the pool."""
        async with self._session_creation_lock:
            initial = len(self._sessions)
            self._sessions = [s for s in self._sessions if await self.validate_session(s)]
            removed = initial - len(self._sessions)
            if removed > 0:
                self._logger.info(f"Removed {removed} dead session(s)")

    # --- Request Execution ---

    async def execute_fetch(self, url: str, headers: dict[str, str], session_index: int | None = None) -> str:
        """Execute a fetch() in the browser context."""
        _, session = await self.get_valid_session(session_index)
        js_script = self._generate_fetch_script("GET", url, headers)
        try:
            return await session.page.evaluate(js_script)
        except PlaywrightError as e:
            self._logger.error(f"Session failed during fetch: {e}")
            await self.invalidate_session(session)
            raise

    def _generate_fetch_script(self, method: str, url: str, headers: dict) -> str:
        """Generate JavaScript for in-browser fetch."""
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

    # --- Cookie Management ---

    async def get_session_cookies(self, session: PlaywrightBrowserSession) -> dict[str, str]:
        """Extract all cookies from a session."""
        cookies = await session.context.cookies()
        return {c["name"]: c["value"] for c in cookies}

    async def set_session_cookies(self, session: PlaywrightBrowserSession, cookies: list[dict]) -> None:
        """Set cookies on a session."""
        await session.context.add_cookies(cookies)

    # --- Page Content ---

    async def get_page_content(self, session_index: int | None = None) -> str:
        """Get the HTML content of the current page."""
        _, session = await self.get_valid_session(session_index)
        try:
            return await session.page.content()
        except PlaywrightError as e:
            self._logger.error(f"Session died during get_page_content: {e}")
            await self.invalidate_session(session)
            raise

    # --- Cleanup ---

    async def close_all(self) -> None:
        """Close all sessions and browser resources."""
        for session in self._sessions:
            try:
                if session.page: await session.page.close()
            except Exception: pass
            try:
                if session.context: await session.context.close()
            except Exception: pass
        self._sessions.clear()
        try:
            if self._browser: await self._browser.close(); self._browser = None
        except Exception: pass
        try:
            if self._playwright: await self._playwright.stop(); self._playwright = None
        except Exception: pass
        self._cleanup_called = True

    # --- Stats ---

    def get_resource_stats(self) -> dict:
        valid = sum(1 for s in self._sessions if s.is_valid)
        return {
            "total_sessions": len(self._sessions), "valid_sessions": valid,
            "invalid_sessions": len(self._sessions) - valid,
            "has_browser": self._browser is not None,
            "has_playwright": self._playwright is not None,
            "cleanup_called": self._cleanup_called,
        }

    async def health_check(self) -> dict:
        health = self.get_resource_stats()
        session_health = []
        for i, session in enumerate(self._sessions):
            is_valid = await self.validate_session(session)
            session_health.append({"index": i, "valid": is_valid})
        health["session_details"] = session_health
        health["healthy_sessions"] = sum(1 for s in session_health if s["valid"])
        return health


def _random_choice(choices: list | None):
    """Return a random choice from a list, or None if empty."""
    if not choices:
        return None
    return random.choice(choices)
