"""Composition root: the only place concrete classes are chosen and wired together."""

from typing import Annotated

from fastapi import Depends, Request

from app.api.container import Container
from app.api.session_cookie import SESSION_COOKIE
from app.core.config import Settings
from app.domain.models import ChatSession, Project
from app.domain.ports import Agent
from app.infrastructure.auth.jwt_tokens import JwtSessionTokens
from app.services.activity_service import ActivityService
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.chat_session_service import ChatSessionService
from app.services.ingestion_service import IngestionService
from app.services.project_review_service import ProjectReviewService
from app.services.project_service import ProjectService
from app.services.project_setup_service import ProjectSetupService
from app.services.user_profile_service import UserProfileService


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
    return AuthService(container.user_registry, tokens, container.password_hasher)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def require_session(request: Request, auth: AuthServiceDep) -> str:
    """Route dependency: the logged-in username, or a 401."""
    return auth.authenticate(request.cookies.get(SESSION_COOKIE))


SessionDep = Annotated[str, Depends(require_session)]


def get_user_profile_service(container: ContainerDep) -> UserProfileService:
    return container.user_profile_service


UserProfileServiceDep = Annotated[UserProfileService, Depends(get_user_profile_service)]


def get_project_service(container: ContainerDep) -> ProjectService:
    return container.project_service


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


def get_project_setup_service(container: ContainerDep) -> ProjectSetupService:
    return container.project_setup_service


ProjectSetupServiceDep = Annotated[ProjectSetupService, Depends(get_project_setup_service)]


async def require_owned_project(
    project_id: str, username: SessionDep, service: ProjectServiceDep
) -> Project:
    """Route dependency for any `/projects/{project_id}/...` route: the project, already confirmed

    to belong to the current user (a 404, not a 403, if it doesn't - see ProjectService).
    """
    return await service.get_owned_project(username, project_id)


OwnedProjectDep = Annotated[Project, Depends(require_owned_project)]


def get_chat_session_service(container: ContainerDep) -> ChatSessionService:
    return container.chat_session_service


ChatSessionServiceDep = Annotated[ChatSessionService, Depends(get_chat_session_service)]


async def require_owned_session(
    project_id: str, session_id: str, username: SessionDep, service: ChatSessionServiceDep
) -> ChatSession:
    """Route dependency for any `/projects/{project_id}/sessions/{session_id}/...` route."""
    return await service.get_owned_session(username, project_id, session_id)


OwnedSessionDep = Annotated[ChatSession, Depends(require_owned_session)]


def get_agent(project: OwnedProjectDep, container: ContainerDep) -> Agent:
    return container.agent_for(project.id)


def get_chat_service(
    agent: Annotated[Agent, Depends(get_agent)], session: OwnedSessionDep, container: ContainerDep
) -> ChatService:
    return ChatService(
        agent,
        container.chat_history,
        session.id,
        activity=container.activity_log,
        project_id=session.project_id,
    )


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]


def get_project_review_service(container: ContainerDep) -> ProjectReviewService:
    return container.project_review_service


ProjectReviewServiceDep = Annotated[ProjectReviewService, Depends(get_project_review_service)]


def get_activity_service(container: ContainerDep) -> ActivityService:
    return container.activity_service


ActivityServiceDep = Annotated[ActivityService, Depends(get_activity_service)]
