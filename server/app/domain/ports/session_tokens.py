from typing import Protocol, runtime_checkable


@runtime_checkable
class SessionTokens(Protocol):
    """Issues and reads the signed token that proves a user is logged in."""

    def issue(self, username: str) -> str: ...

    def read(self, token: str) -> str | None:
        """The username in a valid, unexpired token, else None."""
        ...
