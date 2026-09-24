from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.models import ChatMessage


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class ChatResponse(BaseModel):
    reply: str
    sources: list[str] = []
    tools_used: list[str] = []


class ChatMessageResponse(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    sources: list[str] = []

    @classmethod
    def from_domain(cls, message: ChatMessage) -> "ChatMessageResponse":
        return cls(
            role=message.role,
            content=message.content,
            created_at=message.created_at,
            sources=list(message.sources),
        )


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
