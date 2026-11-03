from datetime import UTC, datetime

import pytest

from app.core.exceptions import NotFoundError
from app.domain.models import ChatSession, Project, User
from app.infrastructure.auth.passwords import hash_password
from app.services.chat_session_service import ChatSessionService
from app.services.project_lifecycle_service import ProjectLifecycleService
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


class FakeProjects:
    def __init__(self) -> None:
        self.projects: dict[str, Project] = {}

    async def get(self, project_id: str) -> Project | None:
        return self.projects.get(project_id)

    async def list_for_owner(self, owner_username: str) -> list[Project]:
        return [p for p in self.projects.values() if p.owner_username == owner_username]

    async def create(self, project: Project) -> None:
        self.projects[project.id] = project

    async def rename(self, project_id: str, name: str) -> Project | None:
        return None

    async def delete(self, project_id: str) -> None:
        self.projects.pop(project_id, None)


class FakeSessions:
    def __init__(self) -> None:
        self.sessions: dict[str, ChatSession] = {}

    async def get(self, session_id: str) -> ChatSession | None:
        return self.sessions.get(session_id)

    async def list_for_project(self, project_id: str) -> list[ChatSession]:
        return [s for s in self.sessions.values() if s.project_id == project_id]

    async def create(self, session: ChatSession) -> None:
        self.sessions[session.id] = session

    async def delete(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)


class FakeContent:
    """Stands in for the ingestion service's clean-up of chunks and files."""

    def __init__(self) -> None:
        self.deleted: list[str] = []

    async def delete_project_content(self, project_id: str) -> None:
        self.deleted.append(project_id)


@pytest.fixture
def projects() -> FakeProjects:
    return FakeProjects()


@pytest.fixture
def project_service(projects: FakeProjects) -> ProjectService:
    return ProjectService(FakeUsers(), projects)


@pytest.fixture
def service(project_service: ProjectService) -> ChatSessionService:
    return ChatSessionService(project_service, FakeSessions())


@pytest.mark.anyio
async def test_create_session_in_an_owned_project(
    service: ChatSessionService, project_service: ProjectService
) -> None:
    project = await project_service.create_project("dev", "My Project")

    session = await service.create_session("dev", project.id, "Session 1")

    assert session.project_id == project.id
    assert session.name == "Session 1"


@pytest.mark.anyio
async def test_create_session_rejects_someone_elses_project(
    service: ChatSessionService, project_service: ProjectService
) -> None:
    project = await project_service.create_project("dev", "Mine")

    with pytest.raises(NotFoundError):
        await service.create_session("someone-else", project.id, "Session 1")


@pytest.mark.anyio
async def test_list_sessions_returns_only_that_projects_sessions(
    service: ChatSessionService, project_service: ProjectService
) -> None:
    project = await project_service.create_project("dev", "Mine")
    other_project = await project_service.create_project("dev", "Other")
    await service.create_session("dev", project.id, "A")
    await service.create_session("dev", other_project.id, "B")

    listed = await service.list_sessions("dev", project.id)

    assert [s.name for s in listed] == ["A"]


@pytest.mark.anyio
async def test_get_owned_session_rejects_a_session_from_a_different_project(
    service: ChatSessionService, project_service: ProjectService
) -> None:
    project = await project_service.create_project("dev", "Mine")
    other_project = await project_service.create_project("dev", "Other")
    session = await service.create_session("dev", other_project.id, "A")

    with pytest.raises(NotFoundError):
        await service.get_owned_session("dev", project.id, session.id)


@pytest.mark.anyio
async def test_get_owned_session_rejects_someone_elses_project(
    service: ChatSessionService, project_service: ProjectService
) -> None:
    project = await project_service.create_project("dev", "Mine")
    session = await service.create_session("dev", project.id, "A")

    with pytest.raises(NotFoundError):
        await service.get_owned_session("someone-else", project.id, session.id)


@pytest.mark.anyio
async def test_get_owned_session_rejects_an_unknown_session(
    service: ChatSessionService, project_service: ProjectService
) -> None:
    project = await project_service.create_project("dev", "Mine")

    with pytest.raises(NotFoundError):
        await service.get_owned_session("dev", project.id, "no-such-session")


class FailingSessions(FakeSessions):
    async def create(self, session: ChatSession) -> None:
        raise OSError("disk full")


@pytest.mark.anyio
async def test_a_new_project_starts_with_session_1(
    service: ChatSessionService, project_service: ProjectService
) -> None:
    lifecycle = ProjectLifecycleService(project_service, service, FakeContent())
    project = await lifecycle.create_project("dev", "Mine")

    assert [s.name for s in await service.list_sessions("dev", project.id)] == ["Session 1"]


@pytest.mark.anyio
async def test_a_project_whose_first_session_fails_is_not_left_behind(
    projects: FakeProjects, project_service: ProjectService
) -> None:
    failing = ChatSessionService(project_service, FailingSessions())
    lifecycle = ProjectLifecycleService(project_service, failing, FakeContent())

    with pytest.raises(OSError):
        await lifecycle.create_project("dev", "Mine")

    assert projects.projects == {}


# --- deletion ---------------------------------------------------------------------------------


@pytest.mark.anyio
async def test_deleting_a_session_keeps_the_others(
    service: ChatSessionService, project_service: ProjectService
) -> None:
    project = await project_service.create_project("dev", "Mine")
    first = await service.create_session("dev", project.id, "A")
    await service.create_session("dev", project.id, "B")

    await service.delete_session("dev", project.id, first.id)

    assert [s.name for s in await service.list_sessions("dev", project.id)] == ["B"]


@pytest.mark.anyio
async def test_deleting_the_last_session_starts_a_fresh_session_1(
    service: ChatSessionService, project_service: ProjectService
) -> None:
    project = await project_service.create_project("dev", "Mine")
    only = await service.create_session("dev", project.id, "Old chat")

    await service.delete_session("dev", project.id, only.id)

    [fresh] = await service.list_sessions("dev", project.id)
    assert (fresh.name, fresh.id != only.id) == ("Session 1", True)


@pytest.mark.anyio
async def test_someone_else_cannot_delete_a_session(
    service: ChatSessionService, project_service: ProjectService
) -> None:
    project = await project_service.create_project("dev", "Mine")
    session = await service.create_session("dev", project.id, "A")

    with pytest.raises(NotFoundError):
        await service.delete_session("someone-else", project.id, session.id)

    assert len(await service.list_sessions("dev", project.id)) == 1


@pytest.mark.anyio
async def test_deleting_a_project_removes_its_content_then_the_project(
    projects: FakeProjects, service: ChatSessionService, project_service: ProjectService
) -> None:
    content = FakeContent()
    lifecycle = ProjectLifecycleService(project_service, service, content)
    project = await lifecycle.create_project("dev", "Mine")

    await lifecycle.delete_project("dev", project.id)

    assert content.deleted == [project.id]
    assert projects.projects == {}


@pytest.mark.anyio
async def test_someone_else_cannot_delete_a_project(
    projects: FakeProjects, service: ChatSessionService, project_service: ProjectService
) -> None:
    content = FakeContent()
    lifecycle = ProjectLifecycleService(project_service, service, content)
    project = await lifecycle.create_project("dev", "Mine")

    with pytest.raises(NotFoundError):
        await lifecycle.delete_project("someone-else", project.id)

    assert content.deleted == []
    assert project.id in projects.projects


@pytest.mark.anyio
async def test_all_of_a_users_project_content_can_be_cleared(
    service: ChatSessionService, project_service: ProjectService
) -> None:
    content = FakeContent()
    lifecycle = ProjectLifecycleService(project_service, service, content)
    first = await lifecycle.create_project("dev", "One")
    second = await lifecycle.create_project("dev", "Two")

    await lifecycle.delete_all_content_for("dev")

    assert sorted(content.deleted) == sorted([first.id, second.id])
