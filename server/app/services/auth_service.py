from datetime import UTC, datetime

from app.core.exceptions import InvalidCredentialsError, UnauthorizedError
from app.domain.models import User
from app.domain.ports import PasswordHasher, SessionTokens, UserRegistry


class AuthService:
    """Looks a login up in the user registry and turns a valid one into a session token."""

    def __init__(
        self, users: UserRegistry, tokens: SessionTokens, passwords: PasswordHasher
    ) -> None:
        self._users = users
        self._tokens = tokens
        self._passwords = passwords

    async def signup(
        self, *, first_name: str, last_name: str, email: str, username: str, password: str
    ) -> str:
        """Creates a new account and logs it straight in. Raises AccountAlreadyExistsError if the

        username or email is already taken.
        """
        user = User(
            username=username,
            password_hash=self._passwords.hash(password),
            first_name=first_name,
            last_name=last_name,
            email=email,
            created_at=datetime.now(UTC),
        )
        await self._users.create(user)
        return self._tokens.issue(user.username)

    async def login(self, username: str, password: str) -> str:
        user = await self._users.get(username)
        # Verify against a real hash either way, so a nonexistent username fails no faster than a
        # wrong password for one that exists.
        password_hash = user.password_hash if user else self._passwords.dummy_hash()
        password_ok = self._passwords.verify(password, password_hash)
        if not (user and password_ok):
            raise InvalidCredentialsError("Invalid username or password.")
        return self._tokens.issue(user.username)

    def authenticate(self, token: str | None) -> str:
        username = self._tokens.read(token) if token else None
        if username is None:
            raise UnauthorizedError("You are not logged in.")
        return username
