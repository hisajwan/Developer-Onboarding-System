"""Deterministic stand-in for a real LLM: no network, no key.

It echoes the start of the prompt, so tests and the UI can see what context the model received.
"""

from app.core.config import Settings

_MAX_ECHO_CHARS = 300


class FakeLLMClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    @classmethod
    def from_settings(cls, settings: Settings) -> "FakeLLMClient":
        return cls()

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        self.calls.append(prompt)
        return "[fake-llm] " + " ".join(prompt.split())[:_MAX_ECHO_CHARS]
