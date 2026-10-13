"""Embedder on Gemini. A large upload is embedded in groups, pausing between them to stay under the
per-minute token limit instead of failing.
"""

import asyncio
from collections.abc import Awaitable, Callable

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import Settings
from app.infrastructure import model_calls
from app.infrastructure.gemini.errors import gemini_errors
from app.infrastructure.provider_registry import require_api_key

_CHARS_PER_TOKEN = 3  # conservative; English averages ~4
_WINDOW_SECONDS = 60.0
_BUDGET_SHARE = 0.8  # headroom, since the token count is an estimate


class GeminiEmbedder:
    def __init__(
        self,
        client: GoogleGenerativeAIEmbeddings,
        model_name: str,
        *,
        tokens_per_minute: int,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._client = client
        self.model_name = model_name
        self._group_budget = max(1, int(tokens_per_minute * _BUDGET_SHARE))
        self._sleep = sleep

    @classmethod
    def from_settings(cls, settings: Settings) -> "GeminiEmbedder":
        client = GoogleGenerativeAIEmbeddings(
            model=f"models/{settings.gemini_embedding_model}",
            google_api_key=require_api_key(settings.gemini_api_key, "GEMINI_API_KEY"),
        )
        return cls(
            client,
            settings.gemini_embedding_model,
            tokens_per_minute=settings.gemini_embedding_tokens_per_minute,
        )

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for position, group in enumerate(self._groups(texts)):
            if position > 0:
                await self._sleep(_WINDOW_SECONDS)
            model_calls.count("gemini", self.model_name, "embed")
            with gemini_errors("embedding document chunks"):
                vectors.extend(await self._client.aembed_documents(group))
        return vectors

    async def embed_query(self, text: str) -> list[float]:
        model_calls.count("gemini", self.model_name, "embed")
        with gemini_errors("embedding the question"):
            return await self._client.aembed_query(text)

    def _groups(self, texts: list[str]) -> list[list[str]]:
        groups: list[list[str]] = []
        current: list[str] = []
        current_tokens = 0
        for text in texts:
            tokens = len(text) // _CHARS_PER_TOKEN + 1
            if current and current_tokens + tokens > self._group_budget:
                groups.append(current)
                current, current_tokens = [], 0
            current.append(text)
            current_tokens += tokens
        if current:
            groups.append(current)
        return groups
