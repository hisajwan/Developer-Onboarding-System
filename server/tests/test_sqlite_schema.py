import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from app.infrastructure.storage.sqlite_schema import SCHEMA_VERSION, connect, ensure_schema
from tests.helpers import seed_parents

T = "2026-01-01T00:00:00+00:00"


def count(path: Path, table: str) -> int:
    with closing(connect(path)) as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def fill_one_project(path: Path) -> None:
    """User "owner" -> project "p1" -> session "s1" -> one message; plus a document and activity."""
    seed_parents(path, projects=("p1",), sessions=())
    with closing(connect(path)) as connection, connection:
        connection.execute(
            "INSERT INTO chat_sessions (id, project_id, name, created_at) "
            "VALUES ('s1', 'p1', 'S', ?)",
            (T,),
        )
        connection.execute(
            "INSERT INTO chat_messages (session_id, role, content, created_at) "
            "VALUES ('s1', 'user', 'hi', ?)",
            (T,),
        )
        connection.execute(
            "INSERT INTO documents VALUES ('p1', 'a.md', 'h', 'sig', 1, ?)", (T,)
        )
        connection.execute(
            "INSERT INTO activity (project_id, kind, source, title, detail, created_at) "
            "VALUES ('p1', 'question', 'ask', 't', 'd', ?)",
            (T,),
        )
        connection.execute("UPDATE users SET last_project_id = 'p1' WHERE username = 'owner'")


def test_a_child_row_needs_its_parent(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    ensure_schema(path)

    with pytest.raises(sqlite3.IntegrityError), closing(connect(path)) as connection:
        connection.execute(
            "INSERT INTO chat_sessions (id, project_id, name, created_at) "
            "VALUES ('s', 'no-such-project', 'S', ?)",
            (T,),
        )


def test_deleting_a_project_removes_everything_under_it(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    fill_one_project(path)

    with closing(connect(path)) as connection, connection:
        connection.execute("DELETE FROM projects WHERE id = 'p1'")

    for table in ("chat_sessions", "chat_messages", "documents", "activity"):
        assert count(path, table) == 0, table
    with closing(connect(path)) as connection:
        last = connection.execute("SELECT last_project_id FROM users WHERE username = 'owner'")
        assert last.fetchone() == (None,)  # cleared, not deleted


def test_deleting_a_user_removes_their_projects(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    fill_one_project(path)

    with closing(connect(path)) as connection, connection:
        connection.execute("DELETE FROM users WHERE username = 'owner'")

    for table in ("projects", "chat_sessions", "chat_messages", "documents", "activity"):
        assert count(path, table) == 0, table


def make_legacy_database(path: Path) -> None:
    """A database as the app wrote it before foreign keys: no keys, no `sources` column, and one
    orphan message whose session is gone."""
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript(
            f"""
            CREATE TABLE users (username TEXT PRIMARY KEY, first_name TEXT NOT NULL,
                last_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL, last_project_id TEXT);
            CREATE TABLE projects (id TEXT PRIMARY KEY, owner_username TEXT NOT NULL,
                name TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE chat_sessions (id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
                name TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE chat_messages (id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL,
                created_at TEXT NOT NULL);
            INSERT INTO users VALUES ('dev', 'D', 'U', 'dev@example.com', 'x', '{T}', 'p1');
            INSERT INTO projects VALUES ('p1', 'dev', 'P', '{T}', '{T}');
            INSERT INTO chat_sessions VALUES ('s1', 'p1', 'S', '{T}');
            INSERT INTO chat_messages (session_id, role, content, created_at)
                VALUES ('s1', 'user', 'kept', '{T}');
            INSERT INTO chat_messages (session_id, role, content, created_at)
                VALUES ('gone', 'user', 'orphan', '{T}');
            """
        )


def test_an_old_database_is_backed_up_and_migrated_keeping_its_rows(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    make_legacy_database(path)

    ensure_schema(path)

    assert (tmp_path / "app.db.before-foreign-keys.bak").is_file()
    with closing(connect(path)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (SCHEMA_VERSION,)
        assert connection.execute("PRAGMA foreign_key_list(chat_sessions)").fetchall()
        rows = connection.execute("SELECT content, sources FROM chat_messages").fetchall()
        assert rows == [("kept", "[]")]  # the orphan is gone; the column was added
        tables = {name for (name,) in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )}
    assert {"documents", "activity"} <= tables
    assert not any(name.endswith("_before_fk") for name in tables)
    assert count(path, "users") == count(path, "projects") == 1


def test_a_migrated_database_cascades_like_a_new_one(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    make_legacy_database(path)
    ensure_schema(path)

    with closing(connect(path)) as connection, connection:
        connection.execute("DELETE FROM projects WHERE id = 'p1'")

    assert count(path, "chat_sessions") == count(path, "chat_messages") == 0
