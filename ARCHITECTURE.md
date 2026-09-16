# TikTikApi Architecture - Hexagonal (Ports & Adapters)

## Overview

This codebase follows **Hexagonal Architecture** (also known as Ports & Adapters), which separates the core business logic from external concerns through well-defined interfaces.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CONSUMERS                                │
│  (Your code, REST API, CLI, tests, scripts)                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FACADE (TikTik.py)                          │
│  TikTikApi - Simple, backward-compatible entry point            │
│  Delegates to the hexagonal architecture internally             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │  VIDEO   │   │  USER    │   │  SOUND   │  ... (8 use cases)
    │ USE CASE │   │ USE CASE │   │ USE CASE │
    └────┬─────┘   └────┬─────┘   └────┬─────┘
         │              │              │
         ▼              ▼              ▼
    ┌──────────────────────────────────────────┐
    │            OUTPUT PORTS                   │
    │  BrowserPort | HttpPort | SigningPort     │
    │  (what the app needs from the outside)    │
    └────┬─────────────┬─────────────┬─────────┘
         │             │             │
         ▼             ▼             ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │Playwright│ │   HTTP   │ │ Signing  │  ← ADAPTERS
    │ Browser  │ │ Adapter  │ │ Adapter  │
    └──────────┘ └──────────┘ └──────────┘
         │             │             │
         ▼             ▼             ▼
    ┌──────────────────────────────────────────┐
    │           EXTERNAL SYSTEMS                │
    │  TikTik.com | Playwright | httpx/requests │
    └──────────────────────────────────────────┘
```

## Layer Responsibilities

### 1. Domain Layer (`TikTikApi/domain/`)

**What it does:** Contains the core business entities and rules.

**Files:**
- `entities.py` - VideoEntity, UserEntity, SoundEntity, HashtagEntity, CommentEntity, PlaylistEntity
- `value_objects.py` - SessionConfig, RequestParams, PaginationCursor, VideoInfo
- `exceptions.py` - Domain-specific exceptions (RequestFailedException, etc.)

**Rules:**
- ZERO external dependencies (no imports from adapters, ports, or infrastructure)
- All entities are dataclasses with factory methods (`from_dict`)
- Entities validate/transform data during construction
- Exceptions represent business rule violations, not HTTP errors

**Why:** Business logic is the most stable part of the system. By keeping it pure, we ensure it works regardless of how data arrives (API, cache, database, test fixtures).

### 2. Ports Layer (`TikTikApi/ports/`)

**What it does:** Defines interface contracts (Protocols) that the application depends on.

**Input Ports (Inbound):**
- `VideoUseCase` - get_video, get_video_info, get_video_comments, etc.
- `UserUseCase` - get_user, get_user_videos, get_user_liked, etc.
- `SoundUseCase` - get_sound, get_sound_videos
- `HashtagUseCase` - get_hashtag, get_hashtag_videos
- `CommentUseCase` - get_comment_replies
- `TrendingUseCase` - get_trending_videos
- `SearchUseCase` - search_users, search_videos
- `PlaylistUseCase` - get_playlist, get_playlist_videos

**Output Ports (Outbound):**
- `BrowserPort` - create_sessions, get_valid_session, execute_fetch, etc.
- `HttpPort` - get_page_content, stream_video, download_video, resolve_redirect
- `SigningPort` - sign_url, generate_x_bogus

**Why:** Ports enforce the Dependency Inversion Principle. The application core defines what it needs (output ports) and what it offers (input ports). Concrete implementations are injected at runtime.

### 3. Application Layer (`TikTikApi/application/`)

**What it does:** Contains use case implementations that orchestrate ports.

**Files:**
- `video_use_case.py` - VideoUseCaseImpl (fetches video info, bytes, comments, related)
- `user_use_case.py` - UserUseCaseImpl (fetches user info, videos, likes, playlists)
- `sound_use_case.py` - SoundUseCaseImpl
- `hashtag_use_case.py` - HashtagUseCaseImpl
- `comment_use_case.py` - CommentUseCaseImpl
- `trending_use_case.py` - TrendingUseCaseImpl
- `search_use_case.py` - SearchUseCaseImpl
- `playlist_use_case.py` - PlaylistUseCaseImpl

**Rules:**
- Each use case receives port interfaces via constructor injection
- Transforms raw data into domain entities
- Handles pagination, retries, and error recovery
- Does NOT know about concrete adapter implementations

**Why:** Use cases contain the orchestration logic that ties everything together. They're testable with mock ports.

### 4. Adapters Layer (`TikTikApi/adapters/`)

**What it does:** Concrete implementations of output port interfaces.

**Files:**
- `playwright_browser.py` - PlaywrightBrowserAdapter (BrowserPort implementation)
- `http_adapter.py` - HttpAdapter (HttpPort implementation)
- `signing_adapter.py` - SigningAdapter (SigningPort implementation)
- `composition_root.py` - CompositionRoot (dependency injection & wiring)

**Rules:**
- Adapters handle ALL infrastructure concerns
- They can be swapped without changing any application or domain code
- The CompositionRoot is the ONLY place that knows about concrete implementations

**Why:** This is where all the "dirty work" lives (browser automation, anti-detection, HTTP). Isolating it keeps the rest of the codebase clean.

### 5. Legacy Layer (`TikTikApi/api/`)

**What it does:** Backward-compatible entity wrappers that delegate to the new architecture.

**Files:**
- `video.py`, `user.py`, `sound.py`, `hashtag.py`, `comment.py`, `trending.py`, `search.py`, `playlist.py`

**Why:** Maintains backward compatibility with existing code while the internal architecture is modernized.

## Data Flow Example

### Fetching a User's Videos

```
1. Consumer calls: api.user(username='therock').videos()
2. User entity (legacy wrapper) calls: self.parent.make_request(...)
3. TikTikApi facade builds the URL, signs it, executes via browser
4. Response is parsed and yielded as Video entities

With hexagonal architecture:
1. Consumer calls: api.user(username='therock').videos()
2. Use case: UserUseCaseImpl.get_user_videos()
3. Use case calls: BrowserPort.get_valid_session()
4. Use case calls: SigningPort.sign_url()
5. Use case calls: BrowserPort.execute_fetch()
6. Use case transforms response to VideoEntity
7. VideoEntity is yielded back to consumer
```

## Testing Strategy

### Unit Tests (Domain Layer)
```python
# Test entities directly - no mocks needed
def test_video_entity_from_dict():
    data = {"id": "123", "createTime": "1690000000", "author": {"uniqueId": "user1"}}
    video = VideoEntity.from_dict(data)
    assert video.id == "123"
    assert video.author.username == "user1"
```

### Use Case Tests (Application Layer)
```python
# Mock the ports, test the orchestration
async def test_get_user_videos():
    mock_browser = MockBrowserPort()
    mock_signing = MockSigningPort()
    use_case = UserUseCaseImpl(browser=mock_browser, signing=mock_signing)
    
    videos = [v async for v in use_case.get_user_videos("therock")]
    assert len(videos) > 0
```

### Integration Tests (Adapter Layer)
```python
# Test real adapters against TikTik
async def test_playwright_adapter():
    adapter = PlaywrightBrowserAdapter()
    config = SessionConfig(headless=True)
    await adapter.create_sessions(num_sessions=1, config=config)
    # ... test actual browser operations
```

## Adding New Features

### Adding a New Entity
1. Define in `domain/entities.py`
2. Add factory method `from_dict`
3. Create input port in `ports/input/`
4. Create use case in `application/use_cases/`
5. Add adapter method in `adapters/` if needed
6. Add facade method in `TikTik.py`

### Adding a New API Endpoint
1. Create/update the input port protocol
2. Implement the use case method
3. The use case calls output ports (browser, signing)
4. No changes needed to adapters unless new infrastructure is required

### Swapping Adapters
```python
# Replace Playwright with Selenium
class SeleniumBrowserAdapter:
    """Implements BrowserPort using Selenium."""
    ...

# In composition root, swap:
root.browser = SeleniumBrowserAdapter()
# Everything else works unchanged
```

## Key Design Decisions

1. **Facade Pattern:** TikTikApi class maintains backward compatibility while delegating to the hexagonal architecture.

2. **Protocol-Based Ports:** Using Python's `typing.Protocol` for structural typing allows duck-typing flexibility while maintaining type safety.

3. **Entity Factory Methods:** `from_dict` class methods centralize data transformation logic.

4. **Composition Root:** Single place for dependency injection makes the dependency graph explicit.

5. **Lazy Pagination:** Use cases yield results via `AsyncIterator` for memory-efficient handling of large result sets.

6. **Session Recovery:** Browser adapter automatically recovers from dead sessions, transparent to the application layer.
