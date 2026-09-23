from fastapi import APIRouter

from app.api.deps import ChatServiceDep
from app.schemas.chat import ChatHistoryResponse, ChatMessageResponse, ChatRequest, ChatResponse

# ChatServiceDep depends on OwnedSessionDep itself, so resolving it already 404s an unowned
# project or a session that isn't one of that project's own.
router = APIRouter(prefix="/projects/{project_id}/sessions/{session_id}", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, service: ChatServiceDep) -> ChatResponse:
    return await service.handle(request)


@router.get("/chat/history", response_model=ChatHistoryResponse)
async def chat_history(service: ChatServiceDep) -> ChatHistoryResponse:
    messages = await service.get_history()
    return ChatHistoryResponse(messages=[ChatMessageResponse.from_domain(m) for m in messages])
