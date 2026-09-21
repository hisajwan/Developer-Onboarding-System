"""Session tokens as signed JWTs (HS256). Stateless, so no session store is needed."""

from datetime import UTC, datetime, timedelta

import jwt
from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import ConfigurationError

_ALGORITHM = "HS256"


class JwtSessionTokens:
    def __init__(self, secret: SecretStr, ttl: timedelta) -> None:
        self._secret = secret
        self._ttl = ttl

    @classmethod
    def from_settings(cls, settings: Settings) -> "JwtSessionTokens":
        if settings.auth_secret is None:
            raise ConfigurationError("Login is not configured: set AUTH_SECRET in server/.env.")
        return cls(settings.auth_secret, timedelta(minutes=settings.session_ttl_minutes))

    def issue(self, username: str) -> str:
        claims = {"sub": username, "exp": datetime.now(UTC) + self._ttl}
        return jwt.encode(claims, self._secret.get_secret_value(), algorithm=_ALGORITHM)

    def read(self, token: str) -> str | None:
        try:
            claims = jwt.decode(token, self._secret.get_secret_value(), algorithms=[_ALGORITHM])
        except jwt.PyJWTError:
            return None
        username = claims.get("sub")
        return username if isinstance(username, str) else None
