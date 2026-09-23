"""SQLite-backed record of projects (built-in `sqlite3`, one small file)."""

import asyncio
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from app.domain.models import Project

_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id             TEXT PRIMARY KEY,
    owner_username TEXT NOT NULL,
    name           TEXT NOT NULL,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
)
"""
_INDEX = "CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_username)"

_COLUMNS = "id, owner_username, name, created_at, updated_at"


class SqliteProjectRegistry:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        with closing(self._connect()) as connection, connection:
            connection.execute(_SCHEMA)
            connection.execute(_INDEX)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    async def get(self, project_id: str) -> Project | None:
        return await asyncio.to_thread(self._get, project_id)

    async def list_for_owner(self, owner_username: str) -> list[Project]:
        return await asyncio.to_thread(self._list_for_owner, owner_username)

    async def create(self, project: Project) -> None:
        await asyncio.to_thread(self._create, project)

    async def rename(self, project_id: str, name: str) -> Project | None:
        return await asyncio.to_thread(self._rename, project_id, name)

    def _get(self, project_id: str) -> Project | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                f"SELECT {_COLUMNS} FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        return _to_project(row) if row else None

    def _list_for_owner(self, owner_username: str) -> list[Project]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                f"SELECT {_COLUMNS} FROM projects WHERE owner_username = ? "
                "ORDER BY created_at DESC, name",
                (owner_username,),
            ).fetchall()
        return [_to_project(row) for row in rows]

    def _create(self, project: Project) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                f"INSERT INTO projects ({_COLUMNS}) VALUES (?, ?, ?, ?, ?)",
                (
                    project.id,
                    project.owner_username,
                    project.name,
                    project.created_at.isoformat(),
                    project.updated_at.isoformat(),
                ),
            )

    def _rename(self, project_id: str, name: str) -> Project | None:
        now = datetime.now(UTC).isoformat()
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                "UPDATE projects SET name = ?, updated_at = ? WHERE id = ?", (name, now, project_id)
            )
            if cursor.rowcount == 0:
                return None
        return self._get(project_id)


def _to_project(row: tuple) -> Project:
    id_, owner_username, name, created_at, updated_at = row
    return Project(
        id=id_,
        owner_username=owner_username,
        name=name,
        created_at=datetime.fromisoformat(created_at),
        updated_at=datetime.fromisoformat(updated_at),
    )
