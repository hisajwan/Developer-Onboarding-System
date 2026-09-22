import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings
from app.main import create_app

# Generated per test run, so no credential-like literal lives in the repo.
USERNAME = "dev"
PASSWORD = secrets.token_urlsafe(12)
SECRET = secrets.token_urlsafe(32)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        environment="test",
        data_dir=tmp_path / "data",  # tests never touch the real data folder
        auth_username=USERNAME,
        auth_password=SecretStr(PASSWORD),
        auth_secret=SecretStr(SECRET),
        _env_file=None,
    )


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
