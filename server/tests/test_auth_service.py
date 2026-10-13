from datetime import UTC, datetime, timedelta

import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import (
    AccountAlreadyExistsError,
    ConfigurationError,
    InvalidCredentialsError,
    UnauthorizedError,
)
from app.domain.models import User
from app.domain.ports import SessionTokens
from app.infrastructure.auth.jwt_tokens import JwtSessionTokens
from app.infrastructure.auth.passwords import BcryptPasswordHasher, hash_password
from app.services.auth_service import AuthService


class FakeTokens:
    """Plain-class fake of the SessionTokens port: 'token-<name>' is valid, anything else is not."""

    def issue(self, username: str) -> str:
        return f"token-{username}"

    def read(self, token: str) -> str | None:
        return token.removeprefix("token-") if token.startswith("token-") else None


class FakeUsers:
    """Plain-class fake of the UserRegistry port, seeded with one account."""

    def __init__(self, username: str = "dev", password: str = "secret") -> None:
        self._by_username: dict[str, User] = {}
        if username:
            self._add(_user(username, password))

    def _add(self, user: User) -> None:
        self._by_username[user.username] = user

    async def get(self, username: str) -> User | None:
        return self._by_username.get(username)

    async def create(self, user: User) -> None:
        if user.username in self._by_username:
            raise AccountAlreadyExistsError("That username is already taken.")
        if any(existing.email == user.email for existing in self._by_username.values()):
            raise AccountAlreadyExistsError("That email is already taken.")
        self._add(user)

    async def record(self, user: User) -> None:
        self._add(user)


def _user(username: str = "dev", password: str = "secret", email: str | None = None) -> User:
    return User(
        username=username,
        password_hash=hash_password(password),
        first_name="Dev",
        last_name="User",
        email=email or f"{username}@example.com",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def service() -> AuthService:
    return AuthService(FakeUsers(), FakeTokens(), BcryptPasswordHasher())


@pytest.mark.anyio
async def test_correct_credentials_give_a_token(service: AuthService) -> None:
    assert await service.login("dev", "secret") == "token-dev"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("username", "password"), [("dev", "wrong"), ("other", "secret"), ("", "")]
)
async def test_any_wrong_credential_is_rejected(
    service: AuthService, username: str, password: str
) -> None:
    with pytest.raises(InvalidCredentialsError):
        await service.login(username, password)


@pytest.mark.anyio
async def test_non_ascii_credentials_are_compared_without_crashing(service: AuthService) -> None:
    with pytest.raises(InvalidCredentialsError):
        await service.login("dév", "sécret")


@pytest.mark.anyio
async def test_a_nonexistent_username_is_rejected_the_same_way_as_a_wrong_password(
    service: AuthService,
) -> None:
    """Both paths run a real bcrypt comparison (see AuthService.login), so a failed login can't be

    used to tell which usernames exist from its response time.
    """
    with pytest.raises(InvalidCredentialsError):
        await service.login("nobody", "whatever")


@pytest.mark.anyio
async def test_signup_creates_an_account_and_logs_it_in(service: AuthService) -> None:
    token = await service.signup(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        username="ada",
        password="s3cret-pass",
    )

    assert token == "token-ada"
    assert service.authenticate(token) == "ada"


@pytest.mark.anyio
async def test_signup_hashes_the_password_rather_than_storing_it(service: AuthService) -> None:
    users = FakeUsers(username="")  # empty registry
    empty_service = AuthService(users, FakeTokens(), BcryptPasswordHasher())

    await empty_service.signup(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        username="ada",
        password="s3cret-pass",
    )

    stored = await users.get("ada")
    assert stored is not None
    assert stored.password_hash != "s3cret-pass"


@pytest.mark.anyio
async def test_signup_rejects_a_username_that_is_already_taken(service: AuthService) -> None:
    with pytest.raises(AccountAlreadyExistsError):
        await service.signup(
            first_name="Someone",
            last_name="Else",
            email="someone-else@example.com",
            username="dev",  # the seeded username
            password="s3cret-pass",
        )


def test_authenticate_returns_the_user_for_a_valid_token(service: AuthService) -> None:
    assert service.authenticate("token-dev") == "dev"


@pytest.mark.parametrize("token", [None, "", "garbage"])
def test_authenticate_rejects_missing_or_invalid_tokens(
    service: AuthService, token: str | None
) -> None:
    with pytest.raises(UnauthorizedError):
        service.authenticate(token)


def test_jwt_tokens_satisfy_the_port_and_round_trip() -> None:
    tokens = JwtSessionTokens(SecretStr("s" * 40), timedelta(minutes=5))

    assert isinstance(tokens, SessionTokens)
    assert tokens.read(tokens.issue("dev")) == "dev"


def test_jwt_tokens_need_a_secret() -> None:
    with pytest.raises(ConfigurationError, match="AUTH_SECRET"):
        JwtSessionTokens.from_settings(Settings(_env_file=None))


def test_a_blank_secret_is_rejected_the_same_as_a_missing_one() -> None:
    """`AUTH_SECRET=` in .env parses as an empty string, not None; it must still fail closed."""
    with pytest.raises(ConfigurationError, match="AUTH_SECRET"):
        JwtSessionTokens.from_settings(Settings(auth_secret=SecretStr("   "), _env_file=None))
