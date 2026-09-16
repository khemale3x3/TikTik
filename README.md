# TikTikApi

Unofficial TikTok API Wrapper in Python with **Hexagonal Architecture**.

Fetch publicly available data from TikTok — videos, users, sounds, hashtags, comments, trending content, search results, and playlists — using browser automation to bypass bot detection.

## Features

- **67 Python files** organized in clean Hexagonal Architecture
- **Async-first** — all methods are `async` for high-performance scraping
- **Anti-detection** — 17 stealth JavaScript patches to avoid bot detection
- **Session pool** — concurrent browser sessions with automatic recovery
- **Proxy support** — smart proxy rotation with pluggable algorithms
- **Backward compatible** — existing `api.video(id=...)` API still works
- **Fully documented** — every module has What/How/Why docstrings

## Quick Start

```bash
pip install TikTikApi
python -m playwright install
```

```python
import asyncio
from TikTikApi import TikTikApi

async def main():
    async with TikTikApi() as api:
        await api.create_sessions(
            num_sessions=3,
            ms_tokens=["your_ms_token_here"]  # Get from browser cookies
        )

        # Get video info
        video = api.video(id="7041997751718137094")
        info = await video.info()
        print(info["desc"])

        # Get user videos
        async for v in api.user(username="therock").videos():
            print(v.id)

        # Get trending
        async for t in api.trending.videos():
            print(t.id)

asyncio.run(main())
```

## Architecture

This project follows **Hexagonal Architecture** (Ports & Adapters):

```
TikTikApi/
├── domain/              # Core entities (zero dependencies)
│   ├── entities.py      # Video, User, Sound, Hashtag, Comment, Playlist
│   ├── value_objects.py # SessionConfig, RequestParams, PaginationCursor
│   └── exceptions.py    # Domain-specific errors
│
├── ports/               # Interface contracts
│   ├── input/           # 8 use case protocols (what the app offers)
│   └── output/          # 3 port protocols (what the app needs)
│
├── adapters/            # Infrastructure implementations
│   ├── playwright_browser.py  # Browser automation adapter
│   ├── http_adapter.py        # HTTP client adapter
│   ├── signing_adapter.py     # X-Bogus request signing
│   └── composition_root.py    # Dependency injection
│
├── application/         # Use case orchestration
│   └── use_cases/       # 8 use case implementations
│
├── api/                 # Legacy backward-compatible wrappers
├── stealth/             # Anti-detection JS injection (17 scripts)
│   └── js/              # Browser fingerprint patches
├── tiktok.py            # Facade (main entry point)
├── exceptions.py        # Exception hierarchy
└── helpers.py           # Utility functions
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.

## API Reference

### Sessions

```python
async with TikTikApi() as api:
    await api.create_sessions(
        num_sessions=5,          # Number of browser sessions
        ms_tokens=["token1"],    # Pre-obtained msTokens
        headless=True,           # Run headless
        browser="chromium",      # chromium/firefox/webkit
        proxies=[...],           # Optional proxy list
        proxy_provider=...,      # Or smart proxy provider
        enable_session_recovery=True,
    )
```

### Video

```python
video = api.video(id="VIDEO_ID")
video = api.video(url="https://www.tiktok.com/@user/video/ID")

info = await video.info()                    # Full video details
video_bytes = await video.bytes()            # Download video
async for chunk in await video.bytes(stream=True):  # Stream video
    process(chunk)
async for comment in video.comments():       # Video comments
    print(comment.text)
async for related in video.related_videos(): # Related videos
    print(related.id)
```

### User

```python
user = api.user(username="therock")

info = await user.info()                     # User profile
async for video in user.videos():            # User's videos
    print(video.id)
async for like in user.liked():              # Liked videos
    print(like.id)
async for playlist in user.playlists():      # User's playlists
    print(playlist.name)
```

### Sound

```python
sound = api.sound(id="SOUND_ID")

info = await sound.info()                    # Sound details
async for video in sound.videos():           # Videos using this sound
    print(video.id)
```

### Hashtag

```python
hashtag = api.hashtag(name="funny")

info = await hashtag.info()                  # Hashtag details
async for video in hashtag.videos():         # Videos with this hashtag
    print(video.id)
```

### Trending

```python
async for video in api.trending.videos():
    print(video.id)
```

### Search

```python
async for user in api.search.users("david teather"):
    print(user.username)
```

### Playlist

```python
playlist = api.playlist(id="PLAYLIST_ID")

info = await playlist.info()                 # Playlist details
async for video in playlist.videos():        # Videos in playlist
    print(video.id)
```

## Advanced Usage

### Custom Adapters (Hexagonal Architecture)

Swap any adapter independently:

```python
from TikTikApi.adapters import PlaywrightBrowserAdapter, HttpAdapter, SigningAdapter
from TikTikApi.adapters.composition_root import CompositionRoot

# Create a custom composition root
root = CompositionRoot.create()

# Replace any adapter
root.http = MyCustomHttpAdapter()

# Access use cases directly
video_entity = await root.video.get_video("some_id")
```

### Domain Entities

Use domain entities directly without the legacy wrappers:

```python
from TikTikApi import VideoEntity, UserEntity

video = VideoEntity.from_dict(raw_tiktok_data)
print(video.id, video.author.username, video.stats)
```

### Session Management

```python
# Health check
health = await api.health_check()
print(health["healthy_sessions"])

# Resource stats
stats = api.get_resource_stats()
print(stats["total_sessions"])
```

### Proxy Provider Integration

```python
from proxyproviders import ProxyProvider

provider = ProxyProvider(api_key="your_key")

async with TikTikApi() as api:
    await api.create_sessions(
        num_sessions=5,
        proxy_provider=provider,
        # proxy_algorithm=RoundRobin()  # Default
    )
```

## Requirements

- Python 3.9+
- Playwright browser binaries (`python -m playwright install`)
- msToken (obtain from browser cookies after visiting TikTok)

## Installation

```bash
pip install TikTikApi
python -m playwright install
```

### Docker

```bash
docker build -t tiktikapi .
docker run -it tiktikapi
```

## Development

```bash
git clone https://github.com/your-repo/TikTik-Api.git
cd TikTik-Api
pip install -r requirements.txt
pip install pytest pytest-asyncio
python -m playwright install

# Run tests
pytest tests/
```

## Testing

Tests require a valid `msToken` environment variable:

```bash
export ms_token="your_token_here"
pytest tests/
```

## Project Structure

| Directory | Purpose |
|-----------|---------|
| `TikTikApi/domain/` | Core business entities and rules (zero dependencies) |
| `TikTikApi/ports/` | Interface contracts (Protocols) |
| `TikTikApi/adapters/` | Infrastructure implementations |
| `TikTikApi/application/` | Use case orchestration |
| `TikTikApi/api/` | Legacy backward-compatible wrappers |
| `TikTikApi/stealth/` | Anti-detection JavaScript injection |
| `tests/` | Integration tests |
| `examples/` | Usage examples |

## License

MIT License

## Contributing

1. Follow the Hexagonal Architecture patterns
2. Add docstrings with What/How/Why format
3. All domain code must have zero external dependencies
4. All adapters must implement the corresponding port protocol
5. Run `pytest tests/` before submitting
