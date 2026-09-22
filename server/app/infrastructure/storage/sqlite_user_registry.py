"""SQLite-backed record of login accounts (built-in `sqlite3`, one small file)."""

import asyncio
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from app.core.exceptions import AccountAlreadyExistsError
from app.domain.models import User

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username        TEXT PRIMARY KEY,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    last_project_id TEXT
)
"""

_COLUMNS = "username, first_name, last_name, email, password_hash, created_at, last_project_id"


class SqliteUserRegistry:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        with closing(self._connect()) as connection, connection:
            connection.execute(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    async def get(self, username: str) -> User | None:
        return await asyncio.to_thread(self._get, username)

    async def create(self, user: User) -> None:
        await asyncio.to_thread(self._create, user)

    async def record(self, user: User) -> None:
        await asyncio.to_thread(self._record, user)

    def _get(self, username: str) -> User | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                f"SELECT {_COLUMNS} FROM users WHERE username = ?", (username,)
            ).fetchone()
        return _to_user(row) if row else None

    def _create(self, user: User) -> None:
        with closing(self._connect()) as connection, connection:
            try:
                connection.execute(
                    f"INSERT INTO users ({_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?)", _values(user)
                )
            except sqlite3.IntegrityError as exc:
                field = "email" if "users.email" in str(exc) else "username"
                raise AccountAlreadyExistsError(f"That {field} is already taken.") from exc

    def _record(self, user: User) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                f"INSERT INTO users ({_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(username) DO UPDATE SET first_name = excluded.first_name, "
                "last_name = excluded.last_name, email = excluded.email, "
                "password_hash = excluded.password_hash, created_at = excluded.created_at, "
                "last_project_id = excluded.last_project_id",
                _values(user),
            )


def _values(user: User) -> tuple:
    return (
        user.username,
        user.first_name,
        user.last_name,
        user.email,
        user.password_hash,
        user.created_at.isoformat(),
        user.last_project_id,
    )


def _to_user(row: tuple) -> User:
    username, first_name, last_name, email, password_hash, created_at, last_project_id = row
    return User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=password_hash,
        created_at=datetime.fromisoformat(created_at),
        last_project_id=last_project_id,
    )
