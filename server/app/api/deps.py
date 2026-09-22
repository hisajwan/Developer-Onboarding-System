"""Composition root: the only place concrete classes are chosen and wired together."""

from typing import Annotated

from fastapi import Depends, Request

from app.agent.tools.registry import ToolRegistry
from app.api.container import Container
from app.api.session_cookie import SESSION_COOKIE
from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.domain.ports import Agent
from app.infrastructure.auth.jwt_tokens import JwtSessionTokens
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.ingestion_service import IngestionService


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(get_app_settings)]


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_tool_registry(container: ContainerDep) -> ToolRegistry:
    return container.tool_registry


def get_agent(container: ContainerDep) -> Agent:
    return container.agent


def get_chat_service(agent: Annotated[Agent, Depends(get_agent)]) -> ChatService:
    return ChatService(agent)


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]


def get_ingestion_service(container: ContainerDep) -> IngestionService:
    return container.ingestion_service


IngestionServiceDep = Annotated[IngestionService, Depends(get_ingestion_service)]


def get_auth_service(settings: SettingsDep) -> AuthService:
    if settings.auth_username is None or settings.auth_password is None:
        raise ConfigurationError(
            "Login is not configured: set AUTH_USERNAME, AUTH_PASSWORD and AUTH_SECRET "
            "in server/.env."
        )
    return AuthService(
        settings.auth_username,
        settings.auth_password.get_secret_value(),
        JwtSessionTokens.from_settings(settings),
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def require_session(request: Request, auth: AuthServiceDep) -> str:
    """Route dependency: the logged-in username, or a 401."""
    return auth.authenticate(request.cookies.get(SESSION_COOKIE))


SessionDep = Annotated[str, Depends(require_session)]
