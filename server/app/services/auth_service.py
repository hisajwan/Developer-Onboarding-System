from hmac import compare_digest

from app.core.exceptions import InvalidCredentialsError, UnauthorizedError
from app.domain.ports import SessionTokens


class AuthService:
    """Checks the one configured user and turns a login into a session token."""

    def __init__(self, username: str, password: str, tokens: SessionTokens) -> None:
        self._username = username
        self._password = password
        self._tokens = tokens

    def login(self, username: str, password: str) -> str:
        # Both comparisons always run, and neither reveals which of the two was wrong.
        username_ok = compare_digest(username.encode(), self._username.encode())
        password_ok = compare_digest(password.encode(), self._password.encode())
        if not (username_ok and password_ok):
            raise InvalidCredentialsError("Invalid username or password.")
        return self._tokens.issue(self._username)

    def authenticate(self, token: str | None) -> str:
        username = self._tokens.read(token) if token else None
        if username is None:
            raise UnauthorizedError("You are not logged in.")
        return username
