"""
Composition Root - Dependency Injection & Wiring

What it does:
    The Composition Root is responsible for creating all adapters, use cases,
    and wiring them together. It's the only place in the application that
    knows about concrete implementations.

How it works:
    1. Creates concrete adapter instances (Playwright, HTTP, Signing)
    2. Injects adapters into use case implementations
    3. Returns a configured facade (TikTikApi) ready for use

Why:
    The Composition Root is a key pattern in hexagonal architecture. Instead
    of scattered `new` / `__init__` calls throughout the codebase, all
    dependency wiring happens in one place. This:
    - Makes the dependency graph explicit and visible
    - Enables easy testing (swap adapters in one place)
    - Prevents circular dependencies
    - Makes it clear what depends on what
"""

from __future__ import annotations

import logging

from ..adapters.playwright_browser import PlaywrightBrowserAdapter
from ..adapters.http_adapter import HttpAdapter
from ..adapters.signing_adapter import SigningAdapter
from ..application.use_cases import (
    VideoUseCaseImpl,
    UserUseCaseImpl,
    SoundUseCaseImpl,
    HashtagUseCaseImpl,
    CommentUseCaseImpl,
    TrendingUseCaseImpl,
    SearchUseCaseImpl,
    PlaylistUseCaseImpl,
)


class CompositionRoot:
    """
    Assembles the full application by creating and wiring all components.

    Usage:
        root = CompositionRoot.create(logger=my_logger)
        # root.video, root.user, etc. are fully wired use cases
    """

    def __init__(self, logger: logging.Logger | None = None):
        self._logger = logger or logging.getLogger(__name__)

        # Create adapters
        self.browser = PlaywrightBrowserAdapter(logger=self._logger)
        self.http = HttpAdapter()
        self.signing = SigningAdapter(self.browser)

        # Create use cases with injected dependencies
        self.video = VideoUseCaseImpl(browser=self.browser, http=self.http, signing=self.signing, logger=self._logger)
        self.user = UserUseCaseImpl(browser=self.browser, signing=self.signing, logger=self._logger)
        self.sound = SoundUseCaseImpl(browser=self.browser, signing=self.signing, logger=self._logger)
        self.hashtag = HashtagUseCaseImpl(browser=self.browser, signing=self.signing, logger=self._logger)
        self.comment = CommentUseCaseImpl(browser=self.browser, signing=self.signing, logger=self._logger)
        self.trending = TrendingUseCaseImpl(browser=self.browser, signing=self.signing, logger=self._logger)
        self.search = SearchUseCaseImpl(browser=self.browser, signing=self.signing, logger=self._logger)
        self.playlist = PlaylistUseCaseImpl(browser=self.browser, signing=self.signing, logger=self._logger)

    @classmethod
    def create(cls, logger: logging.Logger | None = None) -> "CompositionRoot":
        """Factory method to create a fully configured CompositionRoot."""
        return cls(logger=logger)
