"""The one SQLite schema, shared by every table adapter in this folder.

Tables are created parent-first with foreign keys, so the database itself enforces the ownership
chain (user -> project -> sessions -> messages; project -> documents, activity) and deleting a
parent removes its children (`ON DELETE CASCADE`). SQLite leaves foreign keys off unless every
connection turns them on, which `connect` does.

A database created before foreign keys existed (schema version 0) is migrated once: the file is
backed up next to itself, each table is rebuilt with its keys, and rows whose parent no longer
exists are dropped (there should be none; the services always checked ownership).
"""

import sqlite3
import threading
from contextlib import closing
from pathlib import Path

SCHEMA_VERSION = 1

# Parent-first. Each entry: table, CREATE statement, the columns copied when migrating, and the
# condition a migrated row must meet (its parent exists).
_TABLES: list[tuple[str, str, str, str]] = [
    (
        "users",
        """CREATE TABLE IF NOT EXISTS users (
            username        TEXT PRIMARY KEY,
            first_name      TEXT NOT NULL,
            last_name       TEXT NOT NULL,
            email           TEXT NOT NULL UNIQUE,
            password_hash   TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            last_project_id TEXT REFERENCES projects(id) ON DELETE SET NULL
        )""",
        "username, first_name, last_name, email, password_hash, created_at, last_project_id",
        "1",
    ),
    (
        "projects",
        """CREATE TABLE IF NOT EXISTS projects (
            id             TEXT PRIMARY KEY,
            owner_username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
            name           TEXT NOT NULL,
            created_at     TEXT NOT NULL,
            updated_at     TEXT NOT NULL
        )""",
        "id, owner_username, name, created_at, updated_at",
        "owner_username IN (SELECT username FROM users)",
    ),
    (
        "chat_sessions",
        """CREATE TABLE IF NOT EXISTS chat_sessions (
            id         TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            name       TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""",
        "id, project_id, name, created_at",
        "project_id IN (SELECT id FROM projects)",
    ),
    (
        "chat_messages",
        """CREATE TABLE IF NOT EXISTS chat_messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            created_at TEXT NOT NULL,
            sources    TEXT NOT NULL DEFAULT '[]'
        )""",
        "id, session_id, role, content, created_at, sources",
        "session_id IN (SELECT id FROM chat_sessions)",
    ),
    (
        "documents",
        """CREATE TABLE IF NOT EXISTS documents (
            project_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            filename        TEXT NOT NULL,
            content_hash    TEXT NOT NULL,
            index_signature TEXT NOT NULL,
            chunk_count     INTEGER NOT NULL,
            indexed_at      TEXT NOT NULL,
            PRIMARY KEY (project_id, filename)
        )""",
        "project_id, filename, content_hash, index_signature, chunk_count, indexed_at",
        "project_id IN (SELECT id FROM projects)",
    ),
    (
        "activity",
        """CREATE TABLE IF NOT EXISTS activity (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id    TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            kind          TEXT NOT NULL,
            source        TEXT NOT NULL,
            title         TEXT NOT NULL,
            detail        TEXT NOT NULL,
            finding_count INTEGER,
            created_at    TEXT NOT NULL
        )""",
        "id, project_id, kind, source, title, detail, finding_count, created_at",
        "project_id IN (SELECT id FROM projects)",
    ),
]

_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_username)",
    "CREATE INDEX IF NOT EXISTS idx_chat_sessions_project ON chat_sessions(project_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id, id)",
    "CREATE INDEX IF NOT EXISTS idx_activity_project ON activity(project_id, created_at)",
]

_lock = threading.Lock()
_ready: set[Path] = set()


def connect(path: Path) -> sqlite3.Connection:
    """A connection with foreign keys enforced. Every adapter connects through this."""
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def ensure_schema(path: Path) -> None:
    """Creates or migrates the database at `path`, once per process."""
    path = path.resolve()
    with _lock:
        if path in _ready:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path, isolation_level=None)) as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            existing = _existing_tables(connection)
            if version < SCHEMA_VERSION and existing:
                _backup(connection, path)
                _migrate(connection, existing)
            else:
                for _, create, _, _ in _TABLES:
                    connection.execute(create)
                connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            for index in _INDEXES:
                connection.execute(index)
        _ready.add(path)


def _existing_tables(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    return {name for (name,) in rows}


def _backup(connection: sqlite3.Connection, path: Path) -> None:
    backup_path = path.with_name(f"{path.name}.before-foreign-keys.bak")
    if backup_path.exists():
        return
    with closing(sqlite3.connect(backup_path)) as backup:
        connection.backup(backup)


def _migrate(connection: sqlite3.Connection, existing: set[str]) -> None:
    """Rebuilds every table with its foreign keys, in one transaction.

    `legacy_alter_table` stops SQLite from rewriting other tables' references when a table is
    renamed out of the way, so the new tables keep pointing at the new parents.
    """
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("PRAGMA legacy_alter_table = ON")
    connection.execute("BEGIN")
    try:
        if "chat_messages" in existing:
            _add_sources_column_if_missing(connection)
        for table, create, columns, keep in _TABLES:
            if table in existing:
                connection.execute(f"ALTER TABLE {table} RENAME TO {table}_before_fk")
            connection.execute(create)
            if table in existing:
                connection.execute(
                    f"INSERT INTO {table} ({columns}) "
                    f"SELECT {columns} FROM {table}_before_fk WHERE {keep}"
                )
                connection.execute(f"DROP TABLE {table}_before_fk")
        connection.execute(
            "UPDATE users SET last_project_id = NULL "
            "WHERE last_project_id IS NOT NULL AND last_project_id NOT IN (SELECT id FROM projects)"
        )
        if connection.execute("PRAGMA foreign_key_check").fetchall():  # pragma: no cover
            raise RuntimeError("Foreign key migration left rows without a parent.")
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.execute("PRAGMA legacy_alter_table = OFF")
        connection.execute("PRAGMA foreign_keys = ON")


def _add_sources_column_if_missing(connection: sqlite3.Connection) -> None:
    """Databases from before citations were stored lack `chat_messages.sources`."""
    columns = {row[1] for row in connection.execute("PRAGMA table_info(chat_messages)")}
    if "sources" not in columns:
        connection.execute(
            "ALTER TABLE chat_messages ADD COLUMN sources TEXT NOT NULL DEFAULT '[]'"
        )
