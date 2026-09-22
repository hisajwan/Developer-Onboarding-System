"""Gemini vision adapter. Placeholder: the real SDK call is not wired yet."""

from pydantic import SecretStr

from app.core.config import Settings
from app.infrastructure.provider_registry import require_api_key


class GeminiImageCaptioner:
    def __init__(self, api_key: SecretStr) -> None:
        self._api_key = api_key

    @classmethod
    def from_settings(cls, settings: Settings) -> "GeminiImageCaptioner":
        return cls(require_api_key(settings.gemini_api_key, "GEMINI_API_KEY"))

    async def caption(self, image: bytes, mime_type: str) -> str:
        raise NotImplementedError("Gemini image captioning is not implemented yet.")
