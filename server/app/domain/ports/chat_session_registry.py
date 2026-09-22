from typing import Protocol, runtime_checkable

from app.domain.models import ChatSession


@runtime_checkable
class ChatSessionRegistry(Protocol):
    """Stores a project's conversation threads."""

    async def get(self, session_id: str) -> ChatSession | None: ...

    async def list_for_project(self, project_id: str) -> list[ChatSession]:
        """Oldest first."""
        ...

    async def create(self, session: ChatSession) -> None: ...
