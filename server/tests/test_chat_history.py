from pathlib import Path

import pytest

from app.domain.ports import ChatHistory
from app.infrastructure.storage.sqlite_chat_history import SqliteChatHistory


@pytest.fixture
def history(tmp_path: Path) -> SqliteChatHistory:
    return SqliteChatHistory(tmp_path / "db" / "app.db")


def test_history_satisfies_its_port(history: SqliteChatHistory) -> None:
    assert isinstance(history, ChatHistory)


@pytest.mark.anyio
async def test_a_new_project_has_no_history(history: SqliteChatHistory) -> None:
    assert await history.list_for_project("proj-1") == []


@pytest.mark.anyio
async def test_messages_come_back_oldest_first(history: SqliteChatHistory) -> None:
    await history.append("proj-1", "user", "How do I set up?")
    await history.append("proj-1", "assistant", "Run npm install.")

    messages = await history.list_for_project("proj-1")

    assert [(m.role, m.content) for m in messages] == [
        ("user", "How do I set up?"),
        ("assistant", "Run npm install."),
    ]


@pytest.mark.anyio
async def test_history_is_scoped_per_project(history: SqliteChatHistory) -> None:
    await history.append("proj-1", "user", "mine")
    await history.append("proj-2", "user", "theirs")

    assert [m.content for m in await history.list_for_project("proj-1")] == ["mine"]
    assert [m.content for m in await history.list_for_project("proj-2")] == ["theirs"]


@pytest.mark.anyio
async def test_limit_caps_how_many_recent_messages_come_back(history: SqliteChatHistory) -> None:
    for i in range(5):
        await history.append("proj-1", "user", f"message {i}")

    messages = await history.list_for_project("proj-1", limit=2)

    assert [m.content for m in messages] == ["message 3", "message 4"]  # the most recent, in order


@pytest.mark.anyio
async def test_history_survives_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    await SqliteChatHistory(path).append("proj-1", "user", "hello")

    messages = await SqliteChatHistory(path).list_for_project("proj-1")

    assert [m.content for m in messages] == ["hello"]
