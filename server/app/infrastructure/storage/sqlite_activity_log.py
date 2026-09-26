"""SQLite-backed activity log: every question and review per project (built-in `sqlite3`)."""

import asyncio
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from app.domain.models import ActivityEvent, ActivityKind

_SCHEMA = """
CREATE TABLE IF NOT EXISTS activity (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id    TEXT NOT NULL,
    kind          TEXT NOT NULL,
    source        TEXT NOT NULL,
    title         TEXT NOT NULL,
    detail        TEXT NOT NULL,
    finding_count INTEGER,
    created_at    TEXT NOT NULL
)
"""
_INDEX = "CREATE INDEX IF NOT EXISTS idx_activity_project ON activity(project_id, created_at)"
_COLUMNS = "project_id, kind, source, title, detail, finding_count, created_at"


class SqliteActivityLog:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        with closing(self._connect()) as connection, connection:
            connection.execute(_SCHEMA)
            connection.execute(_INDEX)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    async def record(self, event: ActivityEvent) -> None:
        await asyncio.to_thread(self._record, event)

    async def recent(self, project_id: str, limit: int = 10) -> list[ActivityEvent]:
        return await asyncio.to_thread(self._recent, project_id, limit)

    async def count(
        self, project_id: str, kind: ActivityKind, since: datetime | None = None
    ) -> int:
        return await asyncio.to_thread(self._count, project_id, kind, since)

    def _record(self, event: ActivityEvent) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                f"INSERT INTO activity ({_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    event.project_id,
                    event.kind,
                    event.source,
                    event.title,
                    event.detail,
                    event.finding_count,
                    event.created_at.isoformat(),
                ),
            )

    def _recent(self, project_id: str, limit: int) -> list[ActivityEvent]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                f"SELECT {_COLUMNS} FROM activity WHERE project_id = ? ORDER BY id DESC LIMIT ?",
                (project_id, limit),
            ).fetchall()
        return [_to_event(row) for row in rows]

    def _count(self, project_id: str, kind: ActivityKind, since: datetime | None) -> int:
        query = "SELECT COUNT(*) FROM activity WHERE project_id = ? AND kind = ?"
        params: list = [project_id, kind]
        if since is not None:
            query += " AND created_at >= ?"
            params.append(since.isoformat())
        with closing(self._connect()) as connection:
            return connection.execute(query, params).fetchone()[0]


def _to_event(row: tuple) -> ActivityEvent:
    project_id, kind, source, title, detail, finding_count, created_at = row
    return ActivityEvent(
        project_id=project_id,
        kind=kind,
        source=source,
        title=title,
        detail=detail,
        finding_count=finding_count,
        created_at=datetime.fromisoformat(created_at),
    )
