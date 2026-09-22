"""Groq tool-calling chat model. Placeholder: the real SDK call is not wired yet."""

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from pydantic import SecretStr

from app.core.config import Settings
from app.infrastructure.provider_registry import require_api_key


class GroqToolCallingChatModel(BaseChatModel):
    api_key: SecretStr

    @classmethod
    def from_settings(cls, settings: Settings) -> "GroqToolCallingChatModel":
        return cls(api_key=require_api_key(settings.groq_api_key, "GROQ_API_KEY"))

    @property
    def _llm_type(self) -> str:
        return "groq-tool-calling"

    def bind_tools(self, tools: list[Any], *, tool_choice: str | None = None, **kwargs: Any):
        return self.bind(tools=tools)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        raise NotImplementedError("Groq agent generation is not implemented yet.")
