from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from app.domain.models import AgentReply, ChatMessage


@runtime_checkable
class Agent(Protocol):
    """The orchestrator the chat service talks to (implemented by `LangChainAgent`)."""

    async def run(self, message: str, history: Sequence[ChatMessage] = ()) -> AgentReply: ...
