from typing import Protocol, runtime_checkable

from app.domain.models import ToolResult


@runtime_checkable
class Tool(Protocol):
    """One capability the agent can call (e.g. retrieve_and_answer, review_code)."""

    name: str
    description: str

    async def run(self, input_text: str) -> ToolResult: ...
