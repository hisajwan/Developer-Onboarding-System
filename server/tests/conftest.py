import asyncio
import secrets
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings
from app.domain.models import User
from app.infrastructure.auth.passwords import hash_password
from app.infrastructure.storage.sqlite_user_registry import SqliteUserRegistry
from app.main import create_app

# Generated per test run, so no credential-like literal lives in the repo.
USERNAME = "dev"
PASSWORD = secrets.token_urlsafe(12)
SECRET = secrets.token_urlsafe(32)


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
def auth_client(client: TestClient) -> TestClient:
    """Logged in: the session cookie from a real /login is kept by the client."""
    response = client.post("/api/v1/login", json={"username": USERNAME, "password": PASSWORD})
    assert response.status_code == 200
    return client


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
