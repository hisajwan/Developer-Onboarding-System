"""LLMClient on Gemini: plain text in, text out (answers, review judgement)."""

from app.core.config import Settings
from app.infrastructure.gemini.chat import build_gemini_chat
from app.infrastructure.llm.chat_client import ChatLLMClient


class GeminiLLMClient(ChatLLMClient):
    @classmethod
    def from_settings(cls, settings: Settings) -> "GeminiLLMClient":
        return cls(build_gemini_chat(settings))
