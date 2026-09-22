from fastapi import APIRouter

from app.api.deps import ChatServiceDep
from app.schemas.chat import ChatHistoryResponse, ChatMessageResponse, ChatRequest, ChatResponse

# ChatServiceDep depends on OwnedProjectDep itself, so resolving it already 404s an unowned project.
router = APIRouter(prefix="/projects/{project_id}", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, service: ChatServiceDep) -> ChatResponse:
    return await service.handle(request)


@router.get("/chat/history", response_model=ChatHistoryResponse)
async def chat_history(service: ChatServiceDep) -> ChatHistoryResponse:
    messages = await service.get_history()
    return ChatHistoryResponse(messages=[ChatMessageResponse.from_domain(m) for m in messages])
