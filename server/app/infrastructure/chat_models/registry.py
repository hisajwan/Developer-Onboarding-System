"""Maps LLM_PROVIDER to the chat model the agent uses to pick a tool. One knob for both this and

the plain-text LLMClient used inside tools (see infrastructure/llm/registry.py); a new provider
means one adapter class here plus one line, same recipe as the other provider registries.
"""

from collections.abc import Callable

from langchain_core.runnables import Runnable

from app.core.config import Settings
from app.core.exceptions import ModelRateLimitedError
from app.infrastructure.chat_models.fake import FakeToolCallingChatModel
from app.infrastructure.chat_models.gemini import create_gemini_chat_model
from app.infrastructure.chat_models.groq import create_groq_chat_model
from app.infrastructure.chat_models.openrouter import OpenRouterToolCallingChatModel
from app.infrastructure.provider_registry import build_provider

_PROVIDERS: dict[str, Callable[[Settings], Runnable]] = {
    "fake": FakeToolCallingChatModel.from_settings,
    "gemini": create_gemini_chat_model,
    "groq": create_groq_chat_model,
    "openrouter": OpenRouterToolCallingChatModel.from_settings,
}


def create_chat_model(settings: Settings) -> Runnable:
    """The LLM_PROVIDER model, switching to LLM_FALLBACK_PROVIDER (if set) when rate-limited."""
    primary = build_provider("Chat model", settings.llm_provider, _PROVIDERS, settings)
    fallback = settings.llm_fallback_provider
    if not fallback or fallback == settings.llm_provider:
        return primary
    backup = build_provider("Chat model", fallback, _PROVIDERS, settings)
    return primary.with_fallbacks([backup], exceptions_to_handle=(ModelRateLimitedError,))
