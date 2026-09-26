import sqlite3
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
async def test_a_new_session_has_no_history(history: SqliteChatHistory) -> None:
    assert await history.list_for_session("session-1") == []


@pytest.mark.anyio
async def test_messages_come_back_oldest_first(history: SqliteChatHistory) -> None:
    await history.append("session-1", "user", "How do I set up?")
    await history.append("session-1", "assistant", "Run npm install.")

    messages = await history.list_for_session("session-1")

    assert [(m.role, m.content) for m in messages] == [
        ("user", "How do I set up?"),
        ("assistant", "Run npm install."),
    ]


@pytest.mark.anyio
async def test_history_is_scoped_per_session(history: SqliteChatHistory) -> None:
    await history.append("session-1", "user", "mine")
    await history.append("session-2", "user", "theirs")

    assert [m.content for m in await history.list_for_session("session-1")] == ["mine"]
    assert [m.content for m in await history.list_for_session("session-2")] == ["theirs"]


@pytest.mark.anyio
async def test_limit_caps_how_many_recent_messages_come_back(history: SqliteChatHistory) -> None:
    for i in range(5):
        await history.append("session-1", "user", f"message {i}")

    messages = await history.list_for_session("session-1", limit=2)

    assert [m.content for m in messages] == ["message 3", "message 4"]  # the most recent, in order


@pytest.mark.anyio
async def test_history_survives_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    await SqliteChatHistory(path).append("session-1", "user", "hello")

    messages = await SqliteChatHistory(path).list_for_session("session-1")

    assert [m.content for m in messages] == ["hello"]


@pytest.mark.anyio
async def test_an_answers_sources_are_saved_and_read_back(tmp_path: Path) -> None:
    history = SqliteChatHistory(tmp_path / "chat.db")

    await history.append("s", "user", "q")
    await history.append("s", "assistant", "a", ("README.md", "guide.pdf"))

    question, answer = await history.list_for_session("s")
    assert question.sources == ()
    assert answer.sources == ("README.md", "guide.pdf")


@pytest.mark.anyio
async def test_a_database_from_before_sources_were_stored_gets_the_column(tmp_path: Path) -> None:
    path = tmp_path / "old.db"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE chat_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT "
            "NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO chat_messages (session_id, role, content, created_at) "
            "VALUES ('s', 'assistant', 'old answer', '2026-09-23T10:00:00+00:00')"
        )
    connection.close()

    history = SqliteChatHistory(path)
    await history.append("s", "assistant", "new answer", ("README.md",))

    old, new = await history.list_for_session("s")
    assert (old.content, old.sources) == ("old answer", ())
    assert (new.content, new.sources) == ("new answer", ("README.md",))
