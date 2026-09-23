from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.core.exceptions import AccountAlreadyExistsError
from app.domain.models import User
from app.domain.ports import UserRegistry
from app.infrastructure.storage.sqlite_user_registry import SqliteUserRegistry

NOW = datetime(2026, 9, 22, 12, 0, tzinfo=UTC)


def user(
    username: str = "dev",
    password_hash: str = "hash1",
    email: str = "dev@example.com",
    at: datetime = NOW,
) -> User:
    return User(
        username=username,
        password_hash=password_hash,
        first_name="Dev",
        last_name="User",
        email=email,
        created_at=at,
    )


@pytest.fixture
def registry(tmp_path: Path) -> SqliteUserRegistry:
    return SqliteUserRegistry(tmp_path / "db" / "app.db")


def test_registry_satisfies_its_port(registry: SqliteUserRegistry) -> None:
    assert isinstance(registry, UserRegistry)


@pytest.mark.anyio
async def test_registry_round_trips_a_user(registry: SqliteUserRegistry) -> None:
    await registry.record(user())

    assert await registry.get("dev") == user()


@pytest.mark.anyio
async def test_registry_returns_none_for_an_unknown_username(registry: SqliteUserRegistry) -> None:
    assert await registry.get("missing") is None


@pytest.mark.anyio
async def test_recording_the_same_username_replaces_the_entry(
    registry: SqliteUserRegistry,
) -> None:
    await registry.record(user(password_hash="old"))
    await registry.record(user(password_hash="new"))

    assert await registry.get("dev") == user(password_hash="new")


@pytest.mark.anyio
async def test_registry_survives_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    await SqliteUserRegistry(path).record(user())

    assert await SqliteUserRegistry(path).get("dev") == user()


@pytest.mark.anyio
async def test_create_stores_a_new_user(registry: SqliteUserRegistry) -> None:
    await registry.create(user())

    assert await registry.get("dev") == user()


@pytest.mark.anyio
async def test_create_rejects_a_taken_username(registry: SqliteUserRegistry) -> None:
    await registry.create(user())

    with pytest.raises(AccountAlreadyExistsError, match="username"):
        await registry.create(user(email="someone-else@example.com"))


@pytest.mark.anyio
async def test_create_rejects_a_taken_email(registry: SqliteUserRegistry) -> None:
    await registry.create(user())

    with pytest.raises(AccountAlreadyExistsError, match="email"):
        await registry.create(user(username="someone-else"))
