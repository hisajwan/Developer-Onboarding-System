"""Maps LLM_PROVIDER to an adapter. Adding a provider = one adapter class + one line here."""

from collections.abc import Callable

from app.core.config import Settings
from app.domain.ports import LLMClient
from app.infrastructure.llm.fake import FakeLLMClient
from app.infrastructure.llm.fallback import FallbackLLMClient
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
    primary = build_provider("LLM", settings.llm_provider, _PROVIDERS, settings)
    fallback = settings.llm_fallback_provider
    if not fallback or fallback == settings.llm_provider:
        return primary
    return FallbackLLMClient(primary, build_provider("LLM", fallback, _PROVIDERS, settings))
