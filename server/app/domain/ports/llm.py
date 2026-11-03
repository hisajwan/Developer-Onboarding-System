from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    """Text generation. Implemented per provider (Gemini, Groq)."""

    async def generate(self, prompt: str, *, system: str | None = None) -> str: ...
