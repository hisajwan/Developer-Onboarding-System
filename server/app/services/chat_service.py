from app.domain.models import ChatMessage
from app.domain.ports import Agent, ChatHistory
from app.schemas.chat import ChatRequest, ChatResponse


class ChatService:
    """Answers within one project and keeps its conversation, so the agent has memory across

    turns.
    """

    def __init__(self, agent: Agent, history: ChatHistory, project_id: str) -> None:
        self._agent = agent
        self._history = history
        self._project_id = project_id

    async def handle(self, request: ChatRequest) -> ChatResponse:
        past = await self._history.list_for_project(self._project_id)
        reply = await self._agent.run(request.message, past)
        await self._history.append(self._project_id, "user", request.message)
        await self._history.append(self._project_id, "assistant", reply.content)
        return ChatResponse(
            reply=reply.content,
            sources=list(reply.sources),
            tools_used=list(reply.tools_used),
        )

    async def get_history(self) -> list[ChatMessage]:
        return await self._history.list_for_project(self._project_id)
