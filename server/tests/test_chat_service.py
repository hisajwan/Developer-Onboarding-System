from collections.abc import Sequence
from datetime import UTC, datetime

import pytest

from app.domain.models import AgentReply, ChatMessage, ChatRole
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService


class RecordingAgent:
    def __init__(self, reply: AgentReply) -> None:
        self._reply = reply
        self.calls: list[tuple[str, Sequence[ChatMessage]]] = []

    async def run(self, message: str, history: Sequence[ChatMessage] = ()) -> AgentReply:
        self.calls.append((message, history))
        return self._reply


class FakeHistory:
    def __init__(self) -> None:
        self.messages: list[tuple[str, ChatRole, str]] = []

    async def append(self, session_id: str, role: ChatRole, content: str) -> None:
        self.messages.append((session_id, role, content))

    async def list_for_session(self, session_id: str, limit: int = 50) -> list[ChatMessage]:
        now = datetime.now(UTC)
        return [
            ChatMessage(role=role, content=content, created_at=now)
            for sid, role, content in self.messages
            if sid == session_id
        ][-limit:]


@pytest.fixture
def agent() -> RecordingAgent:
    return RecordingAgent(AgentReply(content="Run npm install.", sources=("dev-setup.md",)))


@pytest.fixture
def history() -> FakeHistory:
    return FakeHistory()


@pytest.fixture
def service(agent: RecordingAgent, history: FakeHistory) -> ChatService:
    return ChatService(agent, history, "session-1")


@pytest.mark.anyio
async def test_handle_returns_the_agents_reply(service: ChatService) -> None:
    response = await service.handle(ChatRequest(message="How do I set up?"))

    assert response.reply == "Run npm install."
    assert response.sources == ["dev-setup.md"]


@pytest.mark.anyio
async def test_handle_saves_both_turns_to_history(
    service: ChatService, history: FakeHistory
) -> None:
    await service.handle(ChatRequest(message="How do I set up?"))

    assert history.messages == [
        ("session-1", "user", "How do I set up?"),
        ("session-1", "assistant", "Run npm install."),
    ]


@pytest.mark.anyio
async def test_handle_passes_prior_history_to_the_agent(
    service: ChatService, agent: RecordingAgent, history: FakeHistory
) -> None:
    await history.append("session-1", "user", "earlier question")
    await history.append("session-1", "assistant", "earlier answer")

    await service.handle(ChatRequest(message="a follow-up"))

    [(message, passed_history)] = agent.calls
    assert message == "a follow-up"
    assert [m.content for m in passed_history] == ["earlier question", "earlier answer"]


@pytest.mark.anyio
async def test_handle_does_not_leak_another_sessions_history(
    agent: RecordingAgent, history: FakeHistory
) -> None:
    await history.append("other-session", "user", "not mine")
    service = ChatService(agent, history, "session-1")

    await service.handle(ChatRequest(message="hello"))

    [(_, passed_history)] = agent.calls
    assert passed_history == []


@pytest.mark.anyio
async def test_get_history_returns_this_sessions_saved_messages(
    service: ChatService, history: FakeHistory
) -> None:
    await history.append("session-1", "user", "hi")

    messages = await service.get_history()

    assert [m.content for m in messages] == ["hi"]
