"""Maps LLM_PROVIDER to an adapter. Adding a provider = one adapter class + one line here."""

from collections.abc import Callable

from app.core.config import Settings
from app.domain.ports import LLMClient
from app.infrastructure.llm.fake import FakeLLMClient
from app.infrastructure.llm.gemini import GeminiLLMClient
from app.infrastructure.llm.groq import GroqLLMClient
from app.infrastructure.llm.openrouter import OpenRouterLLMClient
from app.infrastructure.provider_registry import build_provider

_PROVIDERS: dict[str, Callable[[Settings], LLMClient]] = {
    "fake": FakeLLMClient.from_settings,
    "gemini": GeminiLLMClient.from_settings,
    "groq": GroqLLMClient.from_settings,
    "openrouter": OpenRouterLLMClient.from_settings,
}


def create_llm_client(settings: Settings) -> LLMClient:
    return build_provider("LLM", settings.llm_provider, _PROVIDERS, settings)
