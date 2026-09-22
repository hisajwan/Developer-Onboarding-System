"""Maps LLM_PROVIDER to the chat model the agent uses to pick a tool. One knob for both this and

the plain-text LLMClient used inside tools (see infrastructure/llm/registry.py); a new provider
means one adapter class here plus one line, same recipe as the other provider registries.
"""

from collections.abc import Callable

from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import Settings
from app.infrastructure.chat_models.fake import FakeToolCallingChatModel
from app.infrastructure.chat_models.gemini import GeminiToolCallingChatModel
from app.infrastructure.chat_models.groq import GroqToolCallingChatModel
from app.infrastructure.chat_models.openrouter import OpenRouterToolCallingChatModel
from app.infrastructure.provider_registry import build_provider

_PROVIDERS: dict[str, Callable[[Settings], BaseChatModel]] = {
    "fake": FakeToolCallingChatModel.from_settings,
    "gemini": GeminiToolCallingChatModel.from_settings,
    "groq": GroqToolCallingChatModel.from_settings,
    "openrouter": OpenRouterToolCallingChatModel.from_settings,
}


def create_chat_model(settings: Settings) -> BaseChatModel:
    return build_provider("Chat model", settings.llm_provider, _PROVIDERS, settings)
