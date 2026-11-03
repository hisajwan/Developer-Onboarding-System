"""SQLite-backed chat history, so a session's conversation survives a reload and feeds the agent

its memory (built-in `sqlite3`, one small file).
"""

import asyncio
import json
import sqlite3
from collections.abc import Sequence
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from app.domain.models import ChatMessage, ChatRole
from app.infrastructure.storage.sqlite_schema import connect, ensure_schema


class SqliteChatHistory:
    def __init__(self, path: Path) -> None:
        self._path = path
        ensure_schema(path)

    def _connect(self) -> sqlite3.Connection:
        return connect(self._path)

    async def append(
        self, session_id: str, role: ChatRole, content: str, sources: Sequence[str] = ()
    ) -> None:
        await asyncio.to_thread(self._append, session_id, role, content, list(sources))

    async def list_for_session(self, session_id: str, limit: int = 50) -> list[ChatMessage]:
        return await asyncio.to_thread(self._list_for_session, session_id, limit)

    def _append(self, session_id: str, role: ChatRole, content: str, sources: list[str]) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO chat_messages (session_id, role, content, created_at, sources) "
                "VALUES (?, ?, ?, ?, ?)",
                (session_id, role, content, datetime.now(UTC).isoformat(), json.dumps(sources)),
            )

    def _list_for_session(self, session_id: str, limit: int) -> list[ChatMessage]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT role, content, created_at, sources FROM chat_messages WHERE session_id = ? "
                "ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        return [_to_message(row) for row in reversed(rows)]


def _to_message(row: tuple) -> ChatMessage:
    role, content, created_at, sources = row
    return ChatMessage(
        role=role,
        content=content,
        created_at=datetime.fromisoformat(created_at),
        sources=tuple(json.loads(sources)),
    )
