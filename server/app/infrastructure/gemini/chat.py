"""The one Gemini chat model the other Gemini adapters build on (text, agent, captions)."""

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import Settings
from app.core.exceptions import ModelRateLimitedError
from app.infrastructure.gemini.errors import gemini_errors
from app.infrastructure.provider_registry import require_api_key


class GeminiChatModel(ChatGoogleGenerativeAI):
    """ChatGoogleGenerativeAI whose failures surface as the app's own errors."""

    def _generate(self, messages: list[BaseMessage], *args: Any, **kwargs: Any) -> ChatResult:
        with gemini_errors(f"calling {self.model}"):
            return super()._generate(messages, *args, **kwargs)

    async def _agenerate(
        self, messages: list[BaseMessage], *args: Any, **kwargs: Any
    ) -> ChatResult:
        with gemini_errors(f"calling {self.model}"):
            return await super()._agenerate(messages, *args, **kwargs)


def build_gemini_chat(settings: Settings) -> Runnable:
    """The main model, retried on the fallback model (if set) when rate-limited. Forwards
    `bind_tools` to both, so the agent can use it like a chat model."""
    primary = _model(settings, settings.gemini_model)
    if not settings.gemini_fallback_model:
        return primary
    fallback = _model(settings, settings.gemini_fallback_model)
    return primary.with_fallbacks([fallback], exceptions_to_handle=(ModelRateLimitedError,))


def _model(settings: Settings, model: str) -> BaseChatModel:
    return GeminiChatModel(
        model=model,
        google_api_key=require_api_key(settings.gemini_api_key, "GEMINI_API_KEY"),
        temperature=0,
        timeout=settings.gemini_timeout_seconds,
        max_retries=settings.gemini_max_retries,
    )


def message_text(message: BaseMessage) -> str:
    """A reply's text. Newer models may return a list of content parts instead of a string."""
    content = message.content
    if isinstance(content, str):
        return content.strip()
    parts = [
        part if isinstance(part, str) else part.get("text", "")
        for part in content
        if isinstance(part, str) or (isinstance(part, dict) and part.get("type") == "text")
    ]
    return "".join(parts).strip()
