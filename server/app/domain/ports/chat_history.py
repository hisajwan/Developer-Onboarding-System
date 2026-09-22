from typing import Protocol, runtime_checkable

from app.domain.models import ChatMessage, ChatRole


@runtime_checkable
class ChatHistory(Protocol):
    """A project's saved conversation, so the agent's memory and the Ask screen survive a reload."""

    async def append(self, project_id: str, role: ChatRole, content: str) -> None: ...

    async def list_for_project(self, project_id: str, limit: int = 50) -> list[ChatMessage]:
        """Oldest first, capped to the most recent `limit` messages."""
        ...
