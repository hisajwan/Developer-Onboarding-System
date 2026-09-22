"""Composition root: the only place concrete classes are chosen and wired together."""

from typing import Annotated

from fastapi import Depends, Request

from app.api.container import Container
from app.api.session_cookie import SESSION_COOKIE
from app.core.config import Settings
from app.domain.models import Project
from app.domain.ports import Agent
from app.infrastructure.auth.jwt_tokens import JwtSessionTokens
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.ingestion_service import IngestionService
from app.services.project_service import ProjectService


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(get_app_settings)]


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_ingestion_service(container: ContainerDep) -> IngestionService:
    return container.ingestion_service


IngestionServiceDep = Annotated[IngestionService, Depends(get_ingestion_service)]


def get_auth_service(settings: SettingsDep, container: ContainerDep) -> AuthService:
    # Check the signing secret (raises ConfigurationError if missing or blank) before touching the
    # user database, so a config error never has the side effect of creating a data directory.
    tokens = JwtSessionTokens.from_settings(settings)
    return AuthService(container.user_registry, tokens)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def require_session(request: Request, auth: AuthServiceDep) -> str:
    """Route dependency: the logged-in username, or a 401."""
    return auth.authenticate(request.cookies.get(SESSION_COOKIE))


SessionDep = Annotated[str, Depends(require_session)]


def get_project_service(container: ContainerDep) -> ProjectService:
    return container.project_service


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


async def require_owned_project(
    project_id: str, username: SessionDep, service: ProjectServiceDep
) -> Project:
    """Route dependency for any `/projects/{project_id}/...` route: the project, already confirmed

    to belong to the current user (a 404, not a 403, if it doesn't - see ProjectService).
    """
    return await service.get_owned_project(username, project_id)


OwnedProjectDep = Annotated[Project, Depends(require_owned_project)]


def get_agent(project: OwnedProjectDep, container: ContainerDep) -> Agent:
    return container.agent_for(project.id)


def get_chat_service(
    agent: Annotated[Agent, Depends(get_agent)], project: OwnedProjectDep, container: ContainerDep
) -> ChatService:
    return ChatService(agent, container.chat_history, project.id)


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
