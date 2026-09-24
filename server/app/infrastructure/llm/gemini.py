"""LLMClient on Gemini: plain text in, text out (answers, review judgement)."""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable

from app.core.config import Settings
from app.infrastructure.gemini.chat import build_gemini_chat, message_text


class GeminiLLMClient:
    def __init__(self, chat: Runnable) -> None:
        self._chat = chat

    @classmethod
    def from_settings(cls, settings: Settings) -> "GeminiLLMClient":
        return cls(build_gemini_chat(settings))

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        messages = [SystemMessage(content=system)] if system else []
        messages.append(HumanMessage(content=prompt))
        return message_text(await self._chat.ainvoke(messages))
