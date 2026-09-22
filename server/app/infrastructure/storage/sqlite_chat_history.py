"""SQLite-backed chat history, so a project's conversation survives a reload and feeds the agent

its memory (built-in `sqlite3`, one small file).
"""

import asyncio
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from app.domain.models import ChatMessage, ChatRole

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""
_INDEX = "CREATE INDEX IF NOT EXISTS idx_chat_messages_project ON chat_messages(project_id, id)"


class SqliteChatHistory:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        with closing(self._connect()) as connection, connection:
            connection.execute(_SCHEMA)
            connection.execute(_INDEX)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    async def append(self, project_id: str, role: ChatRole, content: str) -> None:
        await asyncio.to_thread(self._append, project_id, role, content)

    async def list_for_project(self, project_id: str, limit: int = 50) -> list[ChatMessage]:
        return await asyncio.to_thread(self._list_for_project, project_id, limit)

    def _append(self, project_id: str, role: ChatRole, content: str) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO chat_messages (project_id, role, content, created_at) "
                "VALUES (?, ?, ?, ?)",
                (project_id, role, content, datetime.now(UTC).isoformat()),
            )

    def _list_for_project(self, project_id: str, limit: int) -> list[ChatMessage]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT role, content, created_at FROM chat_messages WHERE project_id = ? "
                "ORDER BY id DESC LIMIT ?",
                (project_id, limit),
            ).fetchall()
        return [_to_message(row) for row in reversed(rows)]


def _to_message(row: tuple) -> ChatMessage:
    role, content, created_at = row
    return ChatMessage(role=role, content=content, created_at=datetime.fromisoformat(created_at))
