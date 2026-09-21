"""Stand-in agent so the /chat slice works end to end before LangChain is wired in."""

from app.agent.tools.registry import ToolRegistry
from app.domain.models import AgentReply


class PlaceholderAgent:
    def __init__(self, tools: ToolRegistry) -> None:
        self._tools = tools

    async def run(self, message: str) -> AgentReply:
        available = ", ".join(tool.name for tool in self._tools.all()) or "none"
        return AgentReply(content=f"Agent not wired yet. Tools registered: {available}.")
