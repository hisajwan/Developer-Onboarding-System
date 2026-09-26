from collections.abc import Callable
from datetime import UTC, datetime

from app.domain.models import ChatMessage
from app.domain.ports import ActivityLog, Agent, ChatHistory
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.activity_service import question_event, review_event

_REVIEW_TOOL = "review_code"


class ChatService:
    """Answers within one session and keeps its conversation, so the agent has memory across

    turns. The session's project decides which documents it can see; the session itself only
    separates one conversation thread from another within that project.
    """

    def __init__(
        self,
        agent: Agent,
        history: ChatHistory,
        session_id: str,
        *,
        activity: ActivityLog,
        project_id: str,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._agent = agent
        self._history = history
        self._session_id = session_id
        self._activity = activity
        self._project_id = project_id
        self._clock = clock

    async def handle(self, request: ChatRequest) -> ChatResponse:
        past = await self._history.list_for_session(self._session_id)
        reply = await self._agent.run(request.message, past)
        await self._history.append(self._session_id, "user", request.message)
        await self._history.append(self._session_id, "assistant", reply.content, reply.sources)
        await self._activity.record(self._event(request.message, reply.content, reply.tools_used))
        return ChatResponse(
            reply=reply.content,
            sources=list(reply.sources),
            tools_used=list(reply.tools_used),
            retrieved_sources=list(reply.retrieved),
        )

    def _event(self, message: str, reply: str, tools_used: tuple[str, ...]):
        """Code pasted into chat counts as a review, everything else as a question."""
        now = self._clock()
        if _REVIEW_TOOL in tools_used:
            summary = reply.split("\n", 1)[0]
            return review_event(self._project_id, message, summary, now, source="ask")
        return question_event(self._project_id, message, reply, now)

    async def get_history(self) -> list[ChatMessage]:
        return await self._history.list_for_session(self._session_id)
