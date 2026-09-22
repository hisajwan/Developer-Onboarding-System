import pytest

from app.agent.tools.registry import ToolRegistry
from app.core.exceptions import NotFoundError
from app.domain.models import ToolResult


class FakeTool:
    name = "fake"
    description = "A tool for tests."

    async def run(self, input_text: str) -> ToolResult:
        return ToolResult(content=input_text)


def test_registered_tool_can_be_retrieved() -> None:
    registry = ToolRegistry([FakeTool()])

    assert registry.get("fake").name == "fake"


def test_duplicate_registration_is_rejected() -> None:
    registry = ToolRegistry([FakeTool()])

    with pytest.raises(ValueError):
        registry.register(FakeTool())


def test_unknown_tool_raises_not_found() -> None:
    with pytest.raises(NotFoundError):
        ToolRegistry().get("missing")
