"""The LLMClient port over any LangChain chat model: plain text in, text out. Each provider's
adapter only says how to build its chat model."""

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import Runnable


class ChatLLMClient:
    def __init__(self, chat: Runnable) -> None:
        self._chat = chat

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        messages: list[BaseMessage] = [SystemMessage(content=system)] if system else []
        messages.append(HumanMessage(content=prompt))
        return message_text(await self._chat.ainvoke(messages))


def message_text(message: BaseMessage) -> str:
    """A reply's text. Newer models may return a list of content parts instead of a string."""
    content = message.content
    if isinstance(content, str):
        return content.strip()
    parts = [
        part if isinstance(part, str) else part.get("text", "")
        for part in content
        if isinstance(part, str) or (isinstance(part, dict) and part.get("type") == "text")
    ]
    return "".join(parts).strip()
