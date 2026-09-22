"""Gemini embeddings adapter. Placeholder: the real SDK call is not wired yet."""

from pydantic import SecretStr

from app.core.config import Settings
from app.infrastructure.provider_registry import require_api_key


class GeminiEmbedder:
    model_name = "gemini-embedding-001"

    def __init__(self, api_key: SecretStr) -> None:
        self._api_key = api_key

    @classmethod
    def from_settings(cls, settings: Settings) -> "GeminiEmbedder":
        return cls(require_api_key(settings.gemini_api_key, "GEMINI_API_KEY"))

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Gemini embeddings are not implemented yet.")

    async def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError("Gemini embeddings are not implemented yet.")
