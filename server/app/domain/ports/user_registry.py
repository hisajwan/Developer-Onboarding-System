from typing import Protocol, runtime_checkable

from app.domain.models import User


@runtime_checkable
class UserRegistry(Protocol):
    """Looks up and stores login accounts."""

    async def get(self, username: str) -> User | None: ...

    async def create(self, user: User) -> None:
        """Insert a new account; raises AccountAlreadyExistsError if the username or email is

        taken.
        """
        ...

    async def record(self, user: User) -> None:
        """Insert, or replace the entry with the same username - the seed script's password

        reset.
        """
        ...
