from fastapi import APIRouter, Response, status

from app.api.deps import AuthServiceDep, ContainerDep, SessionDep, SettingsDep
from app.api.session_cookie import clear_session_cookie, set_session_cookie
from app.schemas.auth import LoginRequest, SessionResponse, SignupRequest

router = APIRouter(tags=["auth"])


async def _session_response(username: str, container: ContainerDep) -> SessionResponse:
    user = await container.user_registry.get(username)
    last_project_id = user.last_project_id if user else None
    return SessionResponse(username=username, last_project_id=last_project_id)


@router.post("/signup", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    response: Response,
    service: AuthServiceDep,
    settings: SettingsDep,
    container: ContainerDep,
) -> SessionResponse:
    token = await service.signup(
        first_name=request.first_name,
        last_name=request.last_name,
        email=request.email,
        username=request.username,
        password=request.password,
    )
    set_session_cookie(response, token, settings)
    return await _session_response(service.authenticate(token), container)


@router.post("/login", response_model=SessionResponse)
async def login(
    request: LoginRequest,
    response: Response,
    service: AuthServiceDep,
    settings: SettingsDep,
    container: ContainerDep,
) -> SessionResponse:
    token = await service.login(request.username, request.password)
    set_session_cookie(response, token, settings)
    return await _session_response(service.authenticate(token), container)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    clear_session_cookie(response)


@router.get("/session", response_model=SessionResponse)
async def current_session(username: SessionDep, container: ContainerDep) -> SessionResponse:
    return await _session_response(username, container)
