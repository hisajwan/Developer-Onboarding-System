"""The Agent-port implementation: a LangChain tool-calling agent over our own ToolRegistry.

Adding a tool never touches this file — register it in `deps.py`'s container wiring and give it a
sharp `description`, and the model (or the fake, for one tool) picks it up automatically.
"""

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool

from app.agent.tools.registry import ToolRegistry
from app.domain.models import AgentReply, ToolResult
from app.domain.ports import Tool

_SYSTEM_PROMPT = (
    "You are the assistant for this project's onboarding platform. Pick exactly one tool for "
    "each message, choosing by its description, then answer the user using only what that tool "
    "gave you. Never answer from your own knowledge and never call more than one tool."
)

_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM_PROMPT),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)


class LangChainAgent:
    def __init__(self, tools: ToolRegistry, chat_model: BaseChatModel) -> None:
        self._tools = tools
        self._chat_model = chat_model

    async def run(self, message: str) -> AgentReply:
        calls: list[tuple[str, ToolResult]] = []
        langchain_tools = [_as_langchain_tool(tool, calls) for tool in self._tools.all()]
        agent = create_tool_calling_agent(self._chat_model, langchain_tools, _PROMPT)
        executor = AgentExecutor(agent=agent, tools=langchain_tools)

        result = await executor.ainvoke({"input": message})

        sources = tuple(
            dict.fromkeys(source for _, tool_result in calls for source in tool_result.sources)
        )
        tools_used = tuple(dict.fromkeys(name for name, _ in calls))
        return AgentReply(content=result["output"], sources=sources, tools_used=tools_used)


def _as_langchain_tool(tool: Tool, calls: list[tuple[str, ToolResult]]) -> StructuredTool:
    async def call(input: str) -> str:  # noqa: A002 - the schema name the model sees
        result = await tool.run(input)
        calls.append((tool.name, result))
        return result.content

    return StructuredTool.from_function(
        coroutine=call, name=tool.name, description=tool.description
    )
