"""The session cookie: HttpOnly (scripts cannot read it), SameSite=Lax, Secure in production."""

from fastapi import Response

from app.core.config import Settings

SESSION_COOKIE = "session"


def set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_ttl_minutes * 60,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")
