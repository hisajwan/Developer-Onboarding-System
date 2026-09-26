from app.domain.models import Project
from app.services.chat_session_service import ChatSessionService
from app.services.project_service import ProjectService

DEFAULT_SESSION_NAME = "Session 1"


class ProjectSetupService:
    """Creates a project together with its first conversation thread, so Ask mode always has
    somewhere to talk.

    The two rows live in separate tables behind separate ports, so this is not one database
    transaction: if the session can't be created, the project is deleted again rather than left
    behind without a session.
    """

    def __init__(self, projects: ProjectService, sessions: ChatSessionService) -> None:
        self._projects = projects
        self._sessions = sessions

    async def create_project(self, owner_username: str, name: str) -> Project:
        project = await self._projects.create_project(owner_username, name)
        try:
            await self._sessions.create_session(owner_username, project.id, DEFAULT_SESSION_NAME)
        except Exception:
            await self._projects.delete_project(owner_username, project.id)
            raise
        return project
