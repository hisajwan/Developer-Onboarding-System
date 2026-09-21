from typing import Protocol, runtime_checkable

from app.domain.models import AgentReply


@runtime_checkable
class Agent(Protocol):
    """The orchestrator the chat service talks to. Swapped for LangChain later."""

    async def run(self, message: str) -> AgentReply: ...
