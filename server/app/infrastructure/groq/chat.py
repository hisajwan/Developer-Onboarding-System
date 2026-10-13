"""The Groq chat model the Groq adapters build on (plain text and the agent's tool calling)."""

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_groq import ChatGroq

from app.core.config import Settings
from app.infrastructure import model_calls
from app.infrastructure.groq.errors import groq_errors
from app.infrastructure.provider_registry import require_api_key


class GroqChatModel(ChatGroq):
    """ChatGroq whose failures surface as the app's own errors, and whose calls are counted."""

    def _generate(self, messages: list[BaseMessage], *args: Any, **kwargs: Any) -> ChatResult:
        model_calls.count("groq", self.model_name, "chat")
        with groq_errors(f"calling {self.model_name}"):
            return super()._generate(messages, *args, **kwargs)

    async def _agenerate(
        self, messages: list[BaseMessage], *args: Any, **kwargs: Any
    ) -> ChatResult:
        model_calls.count("groq", self.model_name, "chat")
        with groq_errors(f"calling {self.model_name}"):
            return await super()._agenerate(messages, *args, **kwargs)


def build_groq_chat(settings: Settings) -> BaseChatModel:
    return GroqChatModel(
        model=settings.groq_model,
        api_key=require_api_key(settings.groq_api_key, "GROQ_API_KEY"),
        temperature=0,
        timeout=settings.groq_timeout_seconds,
        max_retries=settings.groq_max_retries,
        # See build_gemini_chat: without this the agent's `astream` call bypasses `_agenerate`.
        disable_streaming=True,
    )
