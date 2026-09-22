"""OpenRouter adapter. Placeholder: the real SDK call is not wired yet."""

from pydantic import SecretStr

from app.core.config import Settings
from app.infrastructure.provider_registry import require_api_key


class OpenRouterLLMClient:
    def __init__(self, api_key: SecretStr) -> None:
        self._api_key = api_key

    @classmethod
    def from_settings(cls, settings: Settings) -> "OpenRouterLLMClient":
        return cls(require_api_key(settings.openrouter_api_key, "OPENROUTER_API_KEY"))

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        raise NotImplementedError("OpenRouter generation is not implemented yet.")
