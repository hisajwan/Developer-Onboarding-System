"""Maps LLM_PROVIDER to an adapter. Adding a provider = one adapter class + one line here."""

from collections.abc import Callable

from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.domain.ports import LLMClient
from app.infrastructure.llm.gemini import GeminiLLMClient

_PROVIDERS: dict[str, Callable[[Settings], LLMClient]] = {
    "gemini": GeminiLLMClient.from_settings,
    # "groq": GroqLLMClient.from_settings,
    # "openrouter": OpenRouterLLMClient.from_settings,
}


def create_llm_client(settings: Settings) -> LLMClient:
    builder = _PROVIDERS.get(settings.llm_provider)
    if builder is None:
        raise ConfigurationError(f"LLM provider '{settings.llm_provider}' is not implemented yet.")
    return builder(settings)
