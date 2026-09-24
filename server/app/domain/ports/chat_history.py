from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from app.domain.models import ChatMessage, ChatRole


@runtime_checkable
class ChatHistory(Protocol):
    """A chat session's saved conversation, so the agent's memory and the Ask screen survive a

    reload.
    """

    async def append(
        self, session_id: str, role: ChatRole, content: str, sources: Sequence[str] = ()
    ) -> None: ...

    async def list_for_session(self, session_id: str, limit: int = 50) -> list[ChatMessage]:
        """Oldest first, capped to the most recent `limit` messages."""
        ...
