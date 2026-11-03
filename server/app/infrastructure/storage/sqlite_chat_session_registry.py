"""SQLite-backed record of a project's chat sessions (built-in `sqlite3`, one small file)."""

import asyncio
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from app.domain.models import ChatSession
from app.infrastructure.storage.sqlite_schema import connect, ensure_schema

_COLUMNS = "id, project_id, name, created_at"


class SqliteChatSessionRegistry:
    def __init__(self, path: Path) -> None:
        self._path = path
        ensure_schema(path)

    def _connect(self) -> sqlite3.Connection:
        return connect(self._path)

    async def get(self, session_id: str) -> ChatSession | None:
        return await asyncio.to_thread(self._get, session_id)

    async def list_for_project(self, project_id: str) -> list[ChatSession]:
        return await asyncio.to_thread(self._list_for_project, project_id)

    async def create(self, session: ChatSession) -> None:
        await asyncio.to_thread(self._create, session)

    async def delete(self, session_id: str) -> None:
        await asyncio.to_thread(self._delete, session_id)

    def _delete(self, session_id: str) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))

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
