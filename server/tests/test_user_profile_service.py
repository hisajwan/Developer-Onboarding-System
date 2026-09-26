from datetime import UTC, datetime

import pytest

from app.core.exceptions import InvalidCredentialsError, NotFoundError
from app.domain.models import User
from app.infrastructure.auth.passwords import (
    BcryptPasswordHasher,
    hash_password,
    verify_password,
)
from app.services.user_profile_service import UserProfileService


class FakeUsers:
    def __init__(self) -> None:
        dev = User(
            username="dev",
            password_hash=hash_password("secret"),
            first_name="Dev",
            last_name="User",
            email="dev@example.com",
            created_at=datetime.now(UTC),
        )
        self._users = {"dev": dev}

    async def get(self, username: str) -> User | None:
        return self._users.get(username)

    async def record(self, user: User) -> None:
        self._users[user.username] = user


@pytest.fixture
def users() -> FakeUsers:
    return FakeUsers()


@pytest.fixture
def service(users: FakeUsers) -> UserProfileService:
    return UserProfileService(users, BcryptPasswordHasher())


@pytest.mark.anyio
async def test_get_profile_returns_the_user(service: UserProfileService) -> None:
    profile = await service.get_profile("dev")

    assert profile.first_name == "Dev"
    assert profile.email == "dev@example.com"


@pytest.mark.anyio
async def test_get_profile_rejects_an_unknown_user(service: UserProfileService) -> None:
    with pytest.raises(NotFoundError):
        await service.get_profile("nobody")


@pytest.mark.anyio
async def test_update_profile_changes_the_name(
    service: UserProfileService, users: FakeUsers
) -> None:
    updated = await service.update_profile("dev", "New", "Name")

    assert updated.first_name == "New"
    assert updated.last_name == "Name"
    assert (await users.get("dev")).first_name == "New"


@pytest.mark.anyio
async def test_update_profile_does_not_touch_username_email_or_password(
    service: UserProfileService, users: FakeUsers
) -> None:
    before = await users.get("dev")

    updated = await service.update_profile("dev", "New", "Name")

    assert updated.username == before.username
    assert updated.email == before.email
    assert updated.password_hash == before.password_hash


@pytest.mark.anyio
async def test_change_password_with_the_correct_current_password(
    service: UserProfileService, users: FakeUsers
) -> None:
    await service.change_password("dev", "secret", "new-password-123")

    assert verify_password("new-password-123", (await users.get("dev")).password_hash)
    assert not verify_password("secret", (await users.get("dev")).password_hash)


@pytest.mark.anyio
async def test_change_password_rejects_the_wrong_current_password(
    service: UserProfileService, users: FakeUsers
) -> None:
    with pytest.raises(InvalidCredentialsError):
        await service.change_password("dev", "wrong-password", "new-password-123")

    assert verify_password("secret", (await users.get("dev")).password_hash)  # unchanged
