"""Deterministic stand-in for a tool-calling chat model: no network, no key, no real reasoning.

On the first turn it calls one tool with the user's message: `review_code` if that tool is bound
and the message looks like source code, otherwise the first bound tool. Once the tool's result
comes back, it returns that result's content verbatim as the final answer. The code check is a
rough heuristic so routing can be exercised without a model; how well the real model routes
varied inputs is checked at the integration gate, not here.
"""

import re
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.core.config import Settings

CODE_TOOL = "review_code"

_CODE_SIGNALS = (
    re.compile(r"```"),
    re.compile(r"<[A-Za-z][\w.]*(\s[^<>]*)?/?>"),  # a JSX / HTML tag
    re.compile(r"\b(function|const|let|var|return|import|export|interface|type)\b[^\n]*[=({;]"),
    re.compile(r"=>"),
    re.compile(r"=\{"),  # a JSX attribute expression, e.g. onClick={go}
    re.compile(r"[;{}]\s*$", re.MULTILINE),
)


_DIFF = re.compile(r"^(diff --git |@@ -\d)", re.MULTILINE)


def looks_like_code(text: str) -> bool:
    """True for a fenced block, or for text showing at least two separate signs of code."""
    if "```" in text or _DIFF.search(text):
        return True
    return sum(1 for signal in _CODE_SIGNALS if signal.search(text)) >= 2


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

        names = [tool.name for tool in tools]
        name = CODE_TOOL if CODE_TOOL in names and looks_like_code(question) else names[0]
        call = {"name": name, "args": {"input": question}, "id": "fake-call-1"}
        return _result(AIMessage(content="", tool_calls=[call]))


def _result(message: AIMessage) -> ChatResult:
    return ChatResult(generations=[ChatGeneration(message=message)])
