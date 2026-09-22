from datetime import timedelta

import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, InvalidCredentialsError, UnauthorizedError
from app.domain.ports import SessionTokens
from app.infrastructure.auth.jwt_tokens import JwtSessionTokens
from app.services.auth_service import AuthService


class FakeTokens:
    """Plain-class fake of the SessionTokens port: 'token-<name>' is valid, anything else is not."""

    def issue(self, username: str) -> str:
        return f"token-{username}"

    def read(self, token: str) -> str | None:
        return token.removeprefix("token-") if token.startswith("token-") else None


@pytest.fixture
def service() -> AuthService:
    return AuthService("dev", "secret", FakeTokens())


def test_correct_credentials_give_a_token(service: AuthService) -> None:
    assert service.login("dev", "secret") == "token-dev"


@pytest.mark.parametrize(
    ("username", "password"), [("dev", "wrong"), ("other", "secret"), ("", "")]
)
def test_any_wrong_credential_is_rejected(
    service: AuthService, username: str, password: str
) -> None:
    with pytest.raises(InvalidCredentialsError):
        service.login(username, password)


def test_non_ascii_credentials_are_compared_without_crashing(service: AuthService) -> None:
    with pytest.raises(InvalidCredentialsError):
        service.login("dév", "sécret")


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
