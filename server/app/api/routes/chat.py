from fastapi import APIRouter

from app.api.deps import ChatServiceDep
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, service: ChatServiceDep) -> ChatResponse:
    return await service.handle(request)
