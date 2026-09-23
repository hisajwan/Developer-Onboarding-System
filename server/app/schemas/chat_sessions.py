from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.models import ChatSession


class CreateSessionRequest(BaseModel):
    name: str = Field(default="New session", min_length=1, max_length=200)


class ChatSessionResponse(BaseModel):
    id: str
    name: str
    created_at: datetime

    @classmethod
    def from_domain(cls, session: ChatSession) -> "ChatSessionResponse":
        return cls(id=session.id, name=session.name, created_at=session.created_at)


class ChatSessionListResponse(BaseModel):
    sessions: list[ChatSessionResponse]
