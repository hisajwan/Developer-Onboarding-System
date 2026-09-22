from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.domain.models import ChatSession
from app.domain.ports import ChatSessionRegistry
from app.infrastructure.storage.sqlite_chat_session_registry import SqliteChatSessionRegistry

NOW = datetime(2026, 9, 22, 12, 0, tzinfo=UTC)


def session(
    id_: str = "session-1", project_id: str = "proj-1", name: str = "Session 1", at: datetime = NOW
) -> ChatSession:
    return ChatSession(id=id_, project_id=project_id, name=name, created_at=at)


@pytest.fixture
def registry(tmp_path: Path) -> SqliteChatSessionRegistry:
    return SqliteChatSessionRegistry(tmp_path / "db" / "app.db")


def test_registry_satisfies_its_port(registry: SqliteChatSessionRegistry) -> None:
    assert isinstance(registry, ChatSessionRegistry)


@pytest.mark.anyio
async def test_registry_round_trips_a_session(registry: SqliteChatSessionRegistry) -> None:
    await registry.create(session())

    assert await registry.get("session-1") == session()


@pytest.mark.anyio
async def test_registry_returns_none_for_an_unknown_id(
    registry: SqliteChatSessionRegistry,
) -> None:
    assert await registry.get("missing") is None


@pytest.mark.anyio
async def test_list_for_project_only_returns_that_projects_sessions(
    registry: SqliteChatSessionRegistry,
) -> None:
    await registry.create(session("s1", "proj-1"))
    await registry.create(session("s2", "proj-1"))
    await registry.create(session("s3", "proj-2"))

    listed = await registry.list_for_project("proj-1")

    assert {s.id for s in listed} == {"s1", "s2"}


@pytest.mark.anyio
async def test_list_for_project_with_no_sessions_is_empty(
    registry: SqliteChatSessionRegistry,
) -> None:
    assert await registry.list_for_project("empty-project") == []


@pytest.mark.anyio
async def test_registry_survives_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    await SqliteChatSessionRegistry(path).create(session())

    assert await SqliteChatSessionRegistry(path).get("session-1") == session()
