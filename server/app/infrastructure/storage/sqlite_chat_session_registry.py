"""SQLite-backed record of a project's chat sessions (built-in `sqlite3`, one small file)."""

import asyncio
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from app.domain.models import ChatSession

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    id         TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name       TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""
_INDEX = (
    "CREATE INDEX IF NOT EXISTS idx_chat_sessions_project ON chat_sessions(project_id, created_at)"
)

_COLUMNS = "id, project_id, name, created_at"


class SqliteChatSessionRegistry:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        with closing(self._connect()) as connection, connection:
            connection.execute(_SCHEMA)
            connection.execute(_INDEX)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    async def get(self, session_id: str) -> ChatSession | None:
        return await asyncio.to_thread(self._get, session_id)

    async def list_for_project(self, project_id: str) -> list[ChatSession]:
        return await asyncio.to_thread(self._list_for_project, project_id)

    async def create(self, session: ChatSession) -> None:
        await asyncio.to_thread(self._create, session)

    def _get(self, session_id: str) -> ChatSession | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                f"SELECT {_COLUMNS} FROM chat_sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return _to_session(row) if row else None

    def _list_for_project(self, project_id: str) -> list[ChatSession]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                f"SELECT {_COLUMNS} FROM chat_sessions WHERE project_id = ? ORDER BY created_at",
                (project_id,),
            ).fetchall()
        return [_to_session(row) for row in rows]

    def _create(self, session: ChatSession) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                f"INSERT INTO chat_sessions ({_COLUMNS}) VALUES (?, ?, ?, ?)",
                (session.id, session.project_id, session.name, session.created_at.isoformat()),
            )


def _to_session(row: tuple) -> ChatSession:
    id_, project_id, name, created_at = row
    return ChatSession(
        id=id_, project_id=project_id, name=name, created_at=datetime.fromisoformat(created_at)
    )
