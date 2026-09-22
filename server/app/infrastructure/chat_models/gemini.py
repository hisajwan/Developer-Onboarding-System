"""Gemini tool-calling chat model. Placeholder: the real SDK call is not wired yet."""

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import ConfigurationError


class GeminiToolCallingChatModel(BaseChatModel):
    api_key: SecretStr

    @classmethod
    def from_settings(cls, settings: Settings) -> "GeminiToolCallingChatModel":
        if settings.gemini_api_key is None:
            raise ConfigurationError("GEMINI_API_KEY is not set.")
        return cls(api_key=settings.gemini_api_key)

    @property
    def _llm_type(self) -> str:
        return "gemini-tool-calling"

    def bind_tools(self, tools: list[Any], *, tool_choice: str | None = None, **kwargs: Any):
        return self.bind(tools=tools)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        raise NotImplementedError("Gemini agent generation is not implemented yet.")
