import asyncio
import secrets
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings
from app.domain.models import ChatSession, Project, User
from app.infrastructure.auth.passwords import hash_password
from app.infrastructure.storage.sqlite_chat_session_registry import SqliteChatSessionRegistry
from app.infrastructure.storage.sqlite_project_registry import SqliteProjectRegistry
from app.infrastructure.storage.sqlite_user_registry import SqliteUserRegistry
from app.main import create_app

# Generated per test run, so no credential-like literal lives in the repo.
USERNAME = "dev"
PASSWORD = secrets.token_urlsafe(12)
SECRET = secrets.token_urlsafe(32)
PROJECT_NAME = "Test Project"
SESSION_NAME = "Test Session"


def seed_user(settings: Settings, username: str = USERNAME, password: str = PASSWORD) -> None:
    """Puts a login account straight into the settings' own users table, bypassing HTTP."""
    user = User(
        username=username,
        password_hash=hash_password(password),
        first_name="Dev",
        last_name="User",
        email=f"{username}@example.com",
        created_at=datetime.now(UTC),
    )
    asyncio.run(SqliteUserRegistry(settings.database_path).record(user))


def seed_project(
    settings: Settings, owner_username: str = USERNAME, name: str = PROJECT_NAME
) -> Project:
    """Puts a project straight into the settings' own projects table, bypassing HTTP."""
    now = datetime.now(UTC)
    project = Project(
        id=str(uuid4()), owner_username=owner_username, name=name, created_at=now, updated_at=now
    )
    asyncio.run(SqliteProjectRegistry(settings.database_path).create(project))
    return project


def seed_chat_session(
    settings: Settings, project_id: str, name: str = SESSION_NAME
) -> ChatSession:
    """Puts a chat session straight into the settings' own table, bypassing HTTP."""
    session = ChatSession(
        id=str(uuid4()), project_id=project_id, name=name, created_at=datetime.now(UTC)
    )
    asyncio.run(SqliteChatSessionRegistry(settings.database_path).create(session))
    return session


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    settings = Settings(
        environment="test",
        data_dir=tmp_path / "data",  # tests never touch the real data folder
        auth_secret=SecretStr(SECRET),
        _env_file=None,
    )
    seed_user(settings)
    return settings


@pytest.fixture
def project(settings: Settings) -> Project:
    """A project already owned by the seeded user, for tests of anything project-scoped."""
    return seed_project(settings)


@pytest.fixture
def project_id(project: Project) -> str:
    return project.id


@pytest.fixture
def chat_session(settings: Settings, project: Project) -> ChatSession:
    """A chat session already in the seeded project, for tests of anything chat-scoped."""
    return seed_chat_session(settings, project.id)


@pytest.fixture
def chat_session_id(chat_session: ChatSession) -> str:
    return chat_session.id


@pytest.fixture
def client(settings: Settings) -> TestClient:
    """Not logged in."""
    return TestClient(create_app(settings))


@pytest.fixture
def make_client(settings: Settings):
    """Builds a logged-in client; settings can be overridden, the data folder stays the same."""

    def build(**overrides) -> TestClient:
        client = TestClient(create_app(settings.model_copy(update=overrides)))
        response = client.post("/api/v1/login", json={"username": USERNAME, "password": PASSWORD})
        assert response.status_code == 200
        return client

    return build


@pytest.fixture
def auth_client(client: TestClient, project: Project) -> TestClient:
    """Logged in, with one project already created: the session cookie from a real /login is kept

    by the client.
    """
    response = client.post("/api/v1/login", json={"username": USERNAME, "password": PASSWORD})
    assert response.status_code == 200
    return client


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
