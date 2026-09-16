"""
Stealth Configuration & Application

What it does:
    Contains the StealthConfig dataclass that controls which anti-detection
    scripts are applied, and the stealth_async() function that injects them.

How it works:
    1. StealthConfig defines which scripts to enable (all on by default)
    2. The enabled_scripts property generates JavaScript code
    3. stealth_async() adds each script as a Playwright init script
    4. Scripts run before any page JavaScript, patching browser APIs

Why:
    Each script patches a specific browser API that headless browsers
    expose differently than regular browsers. Together, they make the
    browser context appear to be a normal user browser.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Tuple, Optional, Dict

from playwright.async_api import Page as AsyncPage

# Import stealth JS scripts
from .js.chrome_app import chrome_app
from .js.chrome_csi import chrome_csi
from .js.chrome_hairline import chrome_hairline
from .js.chrome_load_times import chrome_load_times
from .js.chrome_runtime import chrome_runtime
from .js.generate_magic_arrays import generate_magic_arrays
from .js.iframe_contentWindow import iframe_contentWindow
from .js.media_codecs import media_codecs
from .js.navigator_hardwareConcurrency import navigator_hardwareConcurrency
from .js.navigator_languages import navigator_languages
from .js.navigator_permissions import navigator_permissions
from .js.navigator_platform import navigator_platform
from .js.navigator_plugins import navigator_plugins
from .js.navigator_userAgent import navigator_userAgent
from .js.navigator_vendor import navigator_vendor
from .js.webgl_vendor import webgl_vendor
from .js.window_outerdimensions import window_outerdimensions
from .js.utils import utils

SCRIPTS: Dict[str, str] = {
    "chrome_csi": chrome_csi,
    "chrome_app": chrome_app,
    "chrome_runtime": chrome_runtime,
    "chrome_load_times": chrome_load_times,
    "chrome_hairline": chrome_hairline,
    "generate_magic_arrays": generate_magic_arrays,
    "iframe_content_window": iframe_contentWindow,
    "media_codecs": media_codecs,
    "navigator_vendor": navigator_vendor,
    "navigator_plugins": navigator_plugins,
    "navigator_permissions": navigator_permissions,
    "navigator_languages": navigator_languages,
    "navigator_platform": navigator_platform,
    "navigator_user_agent": navigator_userAgent,
    "navigator_hardware_concurrency": navigator_hardwareConcurrency,
    "outerdimensions": window_outerdimensions,
    "utils": utils,
    "webdriver": "delete Object.getPrototypeOf(navigator).webdriver",
    "webgl_vendor": webgl_vendor,
}


@dataclass
class StealthConfig:
    """
    Playwright stealth configuration that applies anti-detection strategies.

    What it does:
        Controls which JavaScript scripts are injected to hide the browser's
        automated nature. Each flag enables/disables a specific patch.

    Attributes:
        webdriver: Remove navigator.webdriver property (detects automation)
        webgl_vendor: Mock WebGL renderer info
        chrome_app: Mock window.chrome.app
        chrome_csi: Mock window.chrome.csi
        chrome_load_times: Mock window.chrome.loadTimes
        chrome_runtime: Mock window.chrome.runtime
        iframe_content_window: Proxy iframe contentWindow access
        media_codecs: Mock media codec support
        navigator_hardware_concurrency: Set CPU core count
        navigator_languages: Override navigator.languages
        navigator_permissions: Proxy navigator.permissions.query
        navigator_platform: Override navigator.platform
        navigator_plugins: Mock browser plugins array
        navigator_user_agent: Override user agent (remove HeadlessChrome)
        navigator_vendor: Override navigator.vendor
        outerdimensions: Mock window.outerWidth/outerHeight
        hairline: Patch offsetHeight for hairline detection
        vendor: WebGL vendor string
        renderer: WebGL renderer string
        nav_vendor: navigator.vendor value
        nav_user_agent: Custom user agent string
        nav_platform: Custom navigator.platform
        languages: Tuple of language strings
        runOnInsecureOrigins: Whether to run on HTTP pages
    """

    # Script toggles
    webdriver: bool = True
    webgl_vendor: bool = True
    chrome_app: bool = True
    chrome_csi: bool = True
    chrome_load_times: bool = True
    chrome_runtime: bool = True
    iframe_content_window: bool = True
    media_codecs: bool = True
    navigator_hardware_concurrency: int = 4
    navigator_languages: bool = False
    navigator_permissions: bool = True
    navigator_platform: bool = True
    navigator_plugins: bool = True
    navigator_user_agent: bool = False
    navigator_vendor: bool = False
    outerdimensions: bool = True
    hairline: bool = True

    # Configuration values
    vendor: str = "Intel Inc."
    renderer: str = "Intel Iris OpenGL Engine"
    nav_vendor: str = "Google Inc."
    nav_user_agent: str = None
    nav_platform: str = None
    languages: Tuple[str] = ("en-US", "en")
    runOnInsecureOrigins: Optional[bool] = None

    @property
    def enabled_scripts(self):
        """Generate JavaScript code for all enabled stealth scripts."""
        opts = json.dumps(
            {
                "webgl_vendor": self.vendor,
                "webgl_renderer": self.renderer,
                "navigator_vendor": self.nav_vendor,
                "navigator_platform": self.nav_platform,
                "navigator_user_agent": self.nav_user_agent,
                "languages": list(self.languages),
                "runOnInsecureOrigins": self.runOnInsecureOrigins,
            }
        )
        yield f"const opts = {opts}"
        yield SCRIPTS["utils"]
        yield SCRIPTS["generate_magic_arrays"]

        if self.chrome_app:
            yield SCRIPTS["chrome_app"]
        if self.chrome_csi:
            yield SCRIPTS["chrome_csi"]
        if self.hairline:
            yield SCRIPTS["chrome_hairline"]
        if self.chrome_load_times:
            yield SCRIPTS["chrome_load_times"]
        if self.chrome_runtime:
            yield SCRIPTS["chrome_runtime"]
        if self.iframe_content_window:
            yield SCRIPTS["iframe_content_window"]
        if self.media_codecs:
            yield SCRIPTS["media_codecs"]
        if self.navigator_languages:
            yield SCRIPTS["navigator_languages"]
        if self.navigator_permissions:
            yield SCRIPTS["navigator_permissions"]
        if self.navigator_platform:
            yield SCRIPTS["navigator_platform"]
        if self.navigator_plugins:
            yield SCRIPTS["navigator_plugins"]
        if self.navigator_user_agent:
            yield SCRIPTS["navigator_user_agent"]
        if self.navigator_vendor:
            yield SCRIPTS["navigator_vendor"]
        if self.webdriver:
            yield SCRIPTS["webdriver"]
        if self.outerdimensions:
            yield SCRIPTS["outerdimensions"]
        if self.webgl_vendor:
            yield SCRIPTS["webgl_vendor"]


async def stealth_async(page: AsyncPage, config: StealthConfig = None):
    """
    Apply stealth scripts to a Playwright page.

    What it does:
        Injects anti-detection JavaScript into the page's init scripts.
        These scripts run before any page JavaScript, patching browser APIs
        to hide the automated nature of the browser.

    Args:
        page: The Playwright page to apply stealth to
        config: Optional StealthConfig (defaults to all patches enabled)
    """
    for script in (config or StealthConfig()).enabled_scripts:
        await page.add_init_script(script)
