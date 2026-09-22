"""Gemini vision adapter. Placeholder: the real SDK call is not wired yet."""

from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import ConfigurationError


class GeminiImageCaptioner:
    def __init__(self, api_key: SecretStr) -> None:
        self._api_key = api_key

    @classmethod
    def from_settings(cls, settings: Settings) -> "GeminiImageCaptioner":
        if settings.gemini_api_key is None:
            raise ConfigurationError("GEMINI_API_KEY is not set.")
        return cls(settings.gemini_api_key)

    async def caption(self, image: bytes, mime_type: str) -> str:
        raise NotImplementedError("Gemini image captioning is not implemented yet.")
