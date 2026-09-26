"""LLMClient on Groq: plain text in, text out (answers, review judgement)."""

from app.core.config import Settings
from app.infrastructure.groq.chat import build_groq_chat
from app.infrastructure.llm.chat_client import ChatLLMClient


class GroqLLMClient(ChatLLMClient):
    @classmethod
    def from_settings(cls, settings: Settings) -> "GroqLLMClient":
        return cls(build_groq_chat(settings))
