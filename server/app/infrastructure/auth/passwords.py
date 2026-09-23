"""bcrypt password hashing, isolated so the rest of the app never imports bcrypt directly."""

import secrets
from functools import lru_cache

import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


@lru_cache(maxsize=1)
def dummy_password_hash() -> str:
    """A valid bcrypt hash of no known password, computed once per process.

    A login for a username that doesn't exist should take about as long as a wrong password for
    one that does - checked against this instead of short-circuiting - so the response time can't
    be used to discover which usernames exist.
    """
    return hash_password(secrets.token_urlsafe(32))
