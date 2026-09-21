from fastapi import APIRouter, Response, status

from app.api.deps import AuthServiceDep, SessionDep, SettingsDep
from app.api.session_cookie import clear_session_cookie, set_session_cookie
from app.schemas.auth import LoginRequest, SessionResponse

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=SessionResponse)
async def login(
    request: LoginRequest,
    response: Response,
    service: AuthServiceDep,
    settings: SettingsDep,
) -> SessionResponse:
    token = service.login(request.username, request.password)
    set_session_cookie(response, token, settings)
    return SessionResponse(username=request.username)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    clear_session_cookie(response)


@router.get("/session", response_model=SessionResponse)
async def current_session(username: SessionDep) -> SessionResponse:
    return SessionResponse(username=username)
