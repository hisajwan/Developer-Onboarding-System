from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.domain.models import Project
from app.domain.ports import ProjectRegistry
from app.infrastructure.storage.sqlite_project_registry import SqliteProjectRegistry

NOW = datetime(2026, 9, 22, 12, 0, tzinfo=UTC)


def project(
    id_: str = "proj-1", owner: str = "dev", name: str = "My Project", at: datetime = NOW
) -> Project:
    return Project(id=id_, owner_username=owner, name=name, created_at=at, updated_at=at)


@pytest.fixture
def registry(tmp_path: Path) -> SqliteProjectRegistry:
    return SqliteProjectRegistry(tmp_path / "db" / "app.db")


def test_registry_satisfies_its_port(registry: SqliteProjectRegistry) -> None:
    assert isinstance(registry, ProjectRegistry)


@pytest.mark.anyio
async def test_registry_round_trips_a_project(registry: SqliteProjectRegistry) -> None:
    await registry.create(project())

    assert await registry.get("proj-1") == project()


@pytest.mark.anyio
async def test_registry_returns_none_for_an_unknown_id(registry: SqliteProjectRegistry) -> None:
    assert await registry.get("missing") is None


@pytest.mark.anyio
async def test_list_for_owner_only_returns_that_owners_projects(
    registry: SqliteProjectRegistry,
) -> None:
    await registry.create(project("p1", owner="dev", at=NOW))
    await registry.create(project("p2", owner="dev", at=NOW + timedelta(hours=1)))
    await registry.create(project("p3", owner="someone-else"))

    listed = await registry.list_for_owner("dev")

    assert [p.id for p in listed] == ["p2", "p1"]  # newest first


@pytest.mark.anyio
async def test_list_for_owner_with_no_projects_is_empty(registry: SqliteProjectRegistry) -> None:
    assert await registry.list_for_owner("nobody") == []


@pytest.mark.anyio
async def test_rename_updates_the_name_and_timestamp(registry: SqliteProjectRegistry) -> None:
    await registry.create(project())

    renamed = await registry.rename("proj-1", "New Name")

    assert renamed is not None
    assert renamed.name == "New Name"
    assert renamed.updated_at >= NOW
    assert (await registry.get("proj-1")).name == "New Name"


@pytest.mark.anyio
async def test_renaming_an_unknown_project_returns_none(registry: SqliteProjectRegistry) -> None:
    assert await registry.rename("missing", "New Name") is None


@pytest.mark.anyio
async def test_delete_removes_the_project_and_ignores_unknown_ids(
    registry: SqliteProjectRegistry,
) -> None:
    await registry.create(project())

    await registry.delete("proj-1")
    await registry.delete("missing")

    assert await registry.get("proj-1") is None


@pytest.mark.anyio
async def test_registry_survives_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    await SqliteProjectRegistry(path).create(project())

    assert await SqliteProjectRegistry(path).get("proj-1") == project()
