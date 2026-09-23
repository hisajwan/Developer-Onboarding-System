from datetime import UTC, datetime
from uuid import uuid4

from app.core.exceptions import NotFoundError
from app.domain.models import ChatSession
from app.domain.ports import ChatSessionRegistry
from app.services.project_service import ProjectService


class ChatSessionService:
    """A project's conversation threads. Ownership is always checked through the project - a

    session with no owned-project match (wrong owner, or belonging to a different project) is
    treated as not found.
    """

    def __init__(self, projects: ProjectService, sessions: ChatSessionRegistry) -> None:
        self._projects = projects
        self._sessions = sessions

    async def create_session(self, owner_username: str, project_id: str, name: str) -> ChatSession:
        await self._projects.get_owned_project(owner_username, project_id)
        session = ChatSession(
            id=str(uuid4()), project_id=project_id, name=name, created_at=datetime.now(UTC)
        )
        await self._sessions.create(session)
        return session

    async def list_sessions(self, owner_username: str, project_id: str) -> list[ChatSession]:
        await self._projects.get_owned_project(owner_username, project_id)
        return await self._sessions.list_for_project(project_id)

    async def get_owned_session(
        self, owner_username: str, project_id: str, session_id: str
    ) -> ChatSession:
        await self._projects.get_owned_project(owner_username, project_id)
        session = await self._sessions.get(session_id)
        if session is None or session.project_id != project_id:
            raise NotFoundError("Session not found.")
        return session
