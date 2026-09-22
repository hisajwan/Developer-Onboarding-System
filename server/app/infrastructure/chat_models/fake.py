"""Deterministic stand-in for a tool-calling chat model: no network, no key, no real reasoning.

On the first turn it always calls the first registered tool with the user's message. Once that
tool's result comes back, it returns that result's content verbatim as the final answer. With a
single tool this reproduces the agent's intended behaviour exactly; once a second tool exists,
picking the right one is what the real model is for (see the fake's own tests for the boundary).
"""

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.core.config import Settings


class FakeToolCallingChatModel(BaseChatModel):
    @classmethod
    def from_settings(cls, settings: Settings) -> "FakeToolCallingChatModel":
        return cls()

    @property
    def _llm_type(self) -> str:
        return "fake-tool-calling"

    def bind_tools(self, tools: list[Any], *, tool_choice: str | None = None, **kwargs: Any):
        return self.bind(tools=tools)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        for message in reversed(messages):
            if isinstance(message, ToolMessage):
                return _result(AIMessage(content=message.content))

        tools = kwargs.get("tools") or []
        if not tools:
            raise RuntimeError("The fake chat model was called with no tools registered.")
        question = next(
            (m.content for m in reversed(messages) if isinstance(m, HumanMessage)), None
        )
        if question is None:
            raise RuntimeError("No user message found to route to a tool.")

        call = {"name": tools[0].name, "args": {"input": question}, "id": "fake-call-1"}
        return _result(AIMessage(content="", tool_calls=[call]))


def _result(message: AIMessage) -> ChatResult:
    return ChatResult(generations=[ChatGeneration(message=message)])
