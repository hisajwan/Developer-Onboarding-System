"""Switches to a second provider when the first one is rate-limited (LLM_FALLBACK_PROVIDER)."""

from app.core.exceptions import ModelRateLimitedError
from app.domain.ports import LLMClient


class FallbackLLMClient:
    def __init__(self, primary: LLMClient, fallback: LLMClient) -> None:
        self._primary = primary
        self._fallback = fallback

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        try:
            return await self._primary.generate(prompt, system=system)
        except ModelRateLimitedError:
            return await self._fallback.generate(prompt, system=system)
