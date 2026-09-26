from typing import Protocol, runtime_checkable

from app.domain.models import Project


@runtime_checkable
class ProjectRegistry(Protocol):
    """Stores projects. One owner each, no membership or roles."""

    async def get(self, project_id: str) -> Project | None: ...

    async def list_for_owner(self, owner_username: str) -> list[Project]:
        """Newest first."""
        ...

    async def create(self, project: Project) -> None: ...

    async def rename(self, project_id: str, name: str) -> Project | None:
        """Renames an existing project and bumps `updated_at`; None if it doesn't exist."""
        ...

    async def delete(self, project_id: str) -> None:
        """Removes the project row; a no-op if it doesn't exist."""
        ...
