"""Gemini adapter. Placeholder: the real SDK call is not wired yet."""

from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import ConfigurationError


class GeminiLLMClient:
    def __init__(self, api_key: SecretStr) -> None:
        self._api_key = api_key

    @classmethod
    def from_settings(cls, settings: Settings) -> "GeminiLLMClient":
        if settings.gemini_api_key is None:
            raise ConfigurationError("GEMINI_API_KEY is not set.")
        return cls(settings.gemini_api_key)

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        raise NotImplementedError("Gemini generation is not implemented yet.")
