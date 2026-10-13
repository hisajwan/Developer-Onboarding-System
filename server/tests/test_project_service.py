from datetime import UTC, datetime

import pytest

from app.core.exceptions import NotFoundError
from app.domain.models import Project, User
from app.infrastructure.auth.passwords import hash_password
from app.services.project_service import ProjectService


class FakeUsers:
    def __init__(self) -> None:
        dev = User(
            username="dev",
            password_hash=hash_password("secret"),
            first_name="Dev",
            last_name="User",
            email="dev@example.com",
            created_at=datetime.now(UTC),
        )
        self._users = {"dev": dev}

    async def get(self, username: str) -> User | None:
        return self._users.get(username)

    async def record(self, user: User) -> None:
        self._users[user.username] = user

    async def create(self, user: User) -> None:
        self._users[user.username] = user


class FakeProjects:
    def __init__(self) -> None:
        self.projects: dict[str, Project] = {}

    async def get(self, project_id: str) -> Project | None:
        return self.projects.get(project_id)

    async def list_for_owner(self, owner_username: str) -> list[Project]:
        matches = [p for p in self.projects.values() if p.owner_username == owner_username]
        return sorted(matches, key=lambda p: p.created_at, reverse=True)

    async def create(self, project: Project) -> None:
        self.projects[project.id] = project

    async def rename(self, project_id: str, name: str) -> Project | None:
        existing = self.projects.get(project_id)
        if existing is None:
            return None
        renamed = Project(
            id=existing.id,
            owner_username=existing.owner_username,
            name=name,
            created_at=existing.created_at,
            updated_at=datetime.now(UTC),
        )
        self.projects[project_id] = renamed
        return renamed

    async def delete(self, project_id: str) -> None:
        self.projects.pop(project_id, None)


@pytest.fixture
def users() -> FakeUsers:
    return FakeUsers()


@pytest.fixture
def service(users: FakeUsers) -> ProjectService:
    return ProjectService(users, FakeProjects())


@pytest.mark.anyio
async def test_create_project_is_owned_by_its_creator(service: ProjectService) -> None:
    project = await service.create_project("dev", "My Project")

    assert project.owner_username == "dev"
    assert project.name == "My Project"


@pytest.mark.anyio
async def test_list_projects_only_returns_that_users_projects(service: ProjectService) -> None:
    await service.create_project("dev", "Mine")
    await service.create_project("someone-else", "Theirs")

    listed = await service.list_projects("dev")

    assert [p.name for p in listed] == ["Mine"]


@pytest.mark.anyio
async def test_rename_project_changes_the_name(service: ProjectService) -> None:
    project = await service.create_project("dev", "Old Name")

    renamed = await service.rename_project("dev", project.id, "New Name")

    assert renamed.name == "New Name"


@pytest.mark.anyio
async def test_rename_project_rejects_someone_elses_project(service: ProjectService) -> None:
    project = await service.create_project("dev", "Mine")

    with pytest.raises(NotFoundError):
        await service.rename_project("someone-else", project.id, "Stolen")


@pytest.mark.anyio
async def test_rename_an_unknown_project_is_not_found(service: ProjectService) -> None:
    with pytest.raises(NotFoundError):
        await service.rename_project("dev", "no-such-project", "New Name")


@pytest.mark.anyio
async def test_get_owned_project_rejects_someone_elses_project(service: ProjectService) -> None:
    project = await service.create_project("dev", "Mine")

    with pytest.raises(NotFoundError):
        await service.get_owned_project("someone-else", project.id)


@pytest.mark.anyio
async def test_select_project_becomes_the_users_last_project(
    service: ProjectService, users: FakeUsers
) -> None:
    project = await service.create_project("dev", "Mine")

    selected = await service.select_project("dev", project.id)

    assert selected.id == project.id
    assert (await users.get("dev")).last_project_id == project.id


@pytest.mark.anyio
async def test_select_project_rejects_a_project_you_do_not_own(service: ProjectService) -> None:
    project = await service.create_project("dev", "Mine")

    with pytest.raises(NotFoundError):
        await service.select_project("someone-else", project.id)
