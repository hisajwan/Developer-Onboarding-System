from app.domain.models import Project
from app.services.chat_session_service import DEFAULT_SESSION_NAME, ChatSessionService
from app.services.ingestion_service import IngestionService
from app.services.project_service import ProjectService


class ProjectLifecycleService:
    """Creates a project with its first conversation thread, and deletes a project with
    everything that belongs to it.

    The SQLite rows under a project (sessions, messages, document registry, activity) go with it
    through foreign keys. Its chunks in the vector store and its files on disk live outside SQLite,
    so they are removed first, explicitly; if that fails, the project is still there to retry.
    """

    def __init__(
        self, projects: ProjectService, sessions: ChatSessionService, content: IngestionService
    ) -> None:
        self._projects = projects
        self._sessions = sessions
        self._content = content

    async def create_project(self, owner_username: str, name: str) -> Project:
        """The two rows are separate writes, so if the session can't be created the project is
        deleted again rather than left behind without a session."""
        project = await self._projects.create_project(owner_username, name)
        try:
            await self._sessions.create_session(owner_username, project.id, DEFAULT_SESSION_NAME)
        except Exception:
            await self._projects.delete_project(owner_username, project.id)
            raise
        return project

    async def delete_project(self, owner_username: str, project_id: str) -> None:
        await self._projects.get_owned_project(owner_username, project_id)
        await self._content.delete_project_content(project_id)
        await self._projects.delete_project(owner_username, project_id)

    async def delete_all_content_for(self, owner_username: str) -> None:
        """Removes the chunks and files of every project this user owns, before the account
        itself is deleted (which takes the project rows with it)."""
        for project in await self._projects.list_projects(owner_username):
            await self._content.delete_project_content(project.id)
