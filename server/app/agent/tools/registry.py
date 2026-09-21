from collections.abc import Iterable

from app.core.exceptions import NotFoundError
from app.domain.ports import Tool


class ToolRegistry:
    """Holds the tools the agent may call, so new tools never touch the agent itself."""

    def __init__(self, tools: Iterable[Tool] = ()) -> None:
        self._tools: dict[str, Tool] = {}
        for tool in tools:
            self.register(tool)

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError:
            raise NotFoundError(f"Unknown tool '{name}'.") from None

    def all(self) -> list[Tool]:
        return list(self._tools.values())
