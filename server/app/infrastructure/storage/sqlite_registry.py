"""SQLite-backed record of indexed documents (built-in `sqlite3`, one small file)."""

import asyncio
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from app.domain.models import IndexedDocument

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    filename        TEXT PRIMARY KEY,
    content_hash    TEXT NOT NULL,
    index_signature TEXT NOT NULL,
    chunk_count     INTEGER NOT NULL,
    indexed_at      TEXT NOT NULL
)
"""


class SqliteDocumentRegistry:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        with closing(self._connect()) as connection, connection:
            connection.execute(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    async def get(self, filename: str) -> IndexedDocument | None:
        return await asyncio.to_thread(self._get, filename)

    async def record(self, document: IndexedDocument) -> None:
        await asyncio.to_thread(self._record, document)

    async def list_all(self) -> list[IndexedDocument]:
        return await asyncio.to_thread(self._list_all)

    def _get(self, filename: str) -> IndexedDocument | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT filename, content_hash, index_signature, chunk_count, indexed_at "
                "FROM documents WHERE filename = ?",
                (filename,),
            ).fetchone()
        return _to_document(row) if row else None

    def _record(self, document: IndexedDocument) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO documents "
                "(filename, content_hash, index_signature, chunk_count, indexed_at) "
                "VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(filename) DO UPDATE SET content_hash = excluded.content_hash, "
                "index_signature = excluded.index_signature, chunk_count = excluded.chunk_count, "
                "indexed_at = excluded.indexed_at",
                (
                    document.filename,
                    document.content_hash,
                    document.index_signature,
                    document.chunk_count,
                    document.indexed_at.isoformat(),
                ),
            )

    def _list_all(self) -> list[IndexedDocument]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT filename, content_hash, index_signature, chunk_count, indexed_at "
                "FROM documents ORDER BY indexed_at DESC, filename"
            ).fetchall()
        return [_to_document(row) for row in rows]


def _to_document(row: tuple) -> IndexedDocument:
    filename, content_hash, index_signature, chunk_count, indexed_at = row
    return IndexedDocument(
        filename=filename,
        content_hash=content_hash,
        index_signature=index_signature,
        chunk_count=chunk_count,
        indexed_at=datetime.fromisoformat(indexed_at),
    )
