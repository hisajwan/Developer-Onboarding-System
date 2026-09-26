"""ImageCaptioner on Gemini's vision input: describes an image so it can be indexed as text."""

import base64

from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable

from app.core.config import Settings
from app.infrastructure.gemini.chat import build_gemini_chat
from app.infrastructure.llm.chat_client import message_text

_PROMPT = (
    "This image comes from a software project's documentation. Describe it so that a developer "
    "could answer questions about it without seeing it: say what kind of image it is (diagram, "
    "screenshot, chart, photo), then list every component, label, arrow or connection and what it "
    "means, and copy any readable text exactly. Plain text, no preamble, at most 250 words."
)


class GeminiImageCaptioner:
    def __init__(self, chat: Runnable) -> None:
        self._chat = chat

    @classmethod
    def from_settings(cls, settings: Settings) -> "GeminiImageCaptioner":
        return cls(build_gemini_chat(settings))

    async def caption(self, image: bytes, mime_type: str) -> str:
        data_url = f"data:{mime_type};base64,{base64.b64encode(image).decode()}"
        message = HumanMessage(
            content=[
                {"type": "text", "text": _PROMPT},
                {"type": "image_url", "image_url": data_url},
            ]
        )
        return message_text(await self._chat.ainvoke([message]))
