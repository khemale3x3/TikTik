"""
Comment Use Case Port - Inbound Interface
"""

from __future__ import annotations

from typing import AsyncIterator, Protocol

from ...domain.entities import CommentEntity


class CommentUseCase(Protocol):
    """Protocol defining comment-related use cases."""

    async def get_comment_replies(
        self, comment_id: str, author_user_id: str, count: int = 20, cursor: int = 0, **kwargs
    ) -> AsyncIterator[CommentEntity]: ...
