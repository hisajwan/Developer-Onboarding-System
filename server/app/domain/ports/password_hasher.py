from typing import Protocol, runtime_checkable


@runtime_checkable
class PasswordHasher(Protocol):
    """Hashes passwords for storage and checks a login against a stored hash."""

    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...

    def dummy_hash(self) -> str:
        """A valid hash of no known password, checked when a username doesn't exist so that
        failing costs the same time either way."""
        ...
