from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from app.core.exceptions import NotFoundError
from app.domain.models import Project
from app.domain.ports import ProjectRegistry, UserRegistry


class ProjectService:
    """Projects are owned by their creator: no membership, no roles, no access requests."""

    def __init__(self, users: UserRegistry, projects: ProjectRegistry) -> None:
        self._users = users
        self._projects = projects

    async def create_project(self, owner_username: str, name: str) -> Project:
        now = datetime.now(UTC)
        project = Project(
            id=str(uuid4()),
            owner_username=owner_username,
            name=name,
            created_at=now,
            updated_at=now,
        )
        await self._projects.create(project)
        return project

    async def delete_project(self, owner_username: str, project_id: str) -> None:
        await self.get_owned_project(owner_username, project_id)
        await self._projects.delete(project_id)

    async def list_projects(self, owner_username: str) -> list[Project]:
        return await self._projects.list_for_owner(owner_username)

    async def rename_project(self, owner_username: str, project_id: str, name: str) -> Project:
        await self.get_owned_project(owner_username, project_id)
        renamed = await self._projects.rename(project_id, name)
        if renamed is None:  # pragma: no cover - can't happen, ownership was just confirmed above
            raise NotFoundError("Project not found.")
        return renamed

    async def select_project(self, owner_username: str, project_id: str) -> Project:
        """Marks this project as the one to restore next time this user logs in."""
        project = await self.get_owned_project(owner_username, project_id)
        user = await self._users.get(owner_username)
        if user is not None:
            await self._users.record(replace(user, last_project_id=project_id))
        return project

    async def get_owned_project(self, owner_username: str, project_id: str) -> Project:
        """The project, if it exists and belongs to this user; raises NotFoundError otherwise.

        Not found and not yours look identical on purpose, so a guessed id can't be used to probe
        for other users' project ids.
        """
        project = await self._projects.get(project_id)
        if project is None or project.owner_username != owner_username:
            raise NotFoundError("Project not found.")
        return project
