from app.domain.ports import Agent
from app.schemas.chat import ChatRequest, ChatResponse


class ChatService:
    def __init__(self, agent: Agent) -> None:
        self._agent = agent

    async def handle(self, request: ChatRequest) -> ChatResponse:
        reply = await self._agent.run(request.message)
        return ChatResponse(
            reply=reply.content,
            sources=list(reply.sources),
            tools_used=list(reply.tools_used),
        )
