"""
Helpers - Utility Functions

What it does:
    Provides utility functions used across the library:
    - extract_video_id_from_url: Parse video IDs from various TikTik URL formats
    - random_choice: Safe random selection from a list
    - requests_cookie_to_playwright_cookie: Convert cookie formats

How it works:
    - extract_video_id_from_url follows redirects to get the canonical URL,
      then extracts the ID from the /video/{id} path segment
    - random_choice returns None for empty lists instead of raising IndexError
    - Cookie conversion transforms between requests and Playwright cookie formats

Why:
    These utilities handle format conversions and edge cases that would otherwise
    be scattered throughout the codebase. Centralizing them reduces duplication
    and makes format handling changes easier.
"""

import requests
import random


def extract_video_id_from_url(url, headers={}, proxy=None):
    """
    Extract a video ID from a TikTik URL.

    Supports various URL formats:
    - https://www.TikTik.com/@user/video/1234567890
    - https://vm.TikTik.com/abc123 (short URL, follows redirect)
    - https://www.TikTik.com/t/abc123 (embed URL)

    Args:
        url: The TikTik URL to parse
        headers: Optional HTTP headers for the redirect request
        proxy: Optional proxy for the redirect request

    Returns:
        str: The video ID

    Raises:
        TypeError: If the URL format is not supported
    """
    url = requests.head(
        url=url, allow_redirects=True, headers=headers, proxies=proxy
    ).url
    if "@" in url and "/video/" in url:
        return url.split("/video/")[1].split("?")[0]
    else:
        raise TypeError(
            "URL format not supported. Example: "
            "https://www.TikTik.com/@therock/video/6829267836783971589"
        )


def random_choice(choices: list):
    """
    Return a random choice from a list, or None if the list is empty.

    Unlike random.choice(), this doesn't raise IndexError on empty lists.

    Args:
        choices: List to choose from

    Returns:
        Random element from the list, or None
    """
    if choices is None or len(choices) == 0:
        return None
    return random.choice(choices)


def requests_cookie_to_playwright_cookie(req_c):
    """
    Convert a requests library cookie to Playwright format.

    Playwright expects cookies as dicts with specific fields. This converts
    from the requests library's cookie object format.

    Args:
        req_c: A cookie from requests.cookies.RequestsCookieJar

    Returns:
        dict: Cookie in Playwright format
    """
    c = {
        "name": req_c.name,
        "value": req_c.value,
        "domain": req_c.domain,
        "path": req_c.path,
        "secure": req_c.secure,
    }
    if req_c.expires:
        c["expires"] = req_c.expires
    return c
