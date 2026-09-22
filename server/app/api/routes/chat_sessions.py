from fastapi import APIRouter, status

from app.api.deps import ChatSessionServiceDep, OwnedProjectDep, SessionDep
from app.schemas.chat_sessions import (
    ChatSessionListResponse,
    ChatSessionResponse,
    CreateSessionRequest,
)

router = APIRouter(prefix="/projects/{project_id}/sessions", tags=["chat-sessions"])


@router.get("", response_model=ChatSessionListResponse)
async def list_sessions(
    project: OwnedProjectDep, username: SessionDep, service: ChatSessionServiceDep
) -> ChatSessionListResponse:
    sessions = await service.list_sessions(username, project.id)
    return ChatSessionListResponse(sessions=[ChatSessionResponse.from_domain(s) for s in sessions])


@router.post("", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    project: OwnedProjectDep,
    username: SessionDep,
    service: ChatSessionServiceDep,
) -> ChatSessionResponse:
    session = await service.create_session(username, project.id, request.name)
    return ChatSessionResponse.from_domain(session)
