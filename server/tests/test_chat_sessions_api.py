from fastapi.testclient import TestClient

from app.core.config import Settings
from tests.conftest import seed_project


def sessions_url(project_id: str) -> str:
    return f"/api/v1/projects/{project_id}/sessions"


def test_sessions_require_login(client: TestClient, project_id: str) -> None:
    assert client.get(sessions_url(project_id)).status_code == 401


def test_creating_a_project_creates_a_default_session(auth_client: TestClient) -> None:
    project = auth_client.post("/api/v1/projects", json={"name": "New Project"}).json()

    sessions = auth_client.get(sessions_url(project["id"])).json()["sessions"]

    assert len(sessions) == 1
    assert sessions[0]["name"] == "Session 1"


def test_create_an_additional_session(auth_client: TestClient, project_id: str) -> None:
    # project_id here is seeded straight into the DB (see conftest.seed_project), bypassing the
    # route that auto-creates "Session 1" - so it starts with no sessions of its own.
    response = auth_client.post(sessions_url(project_id), json={"name": "Second session"})

    assert response.status_code == 201
    assert response.json()["name"] == "Second session"

    listed = auth_client.get(sessions_url(project_id)).json()["sessions"]
    assert {s["name"] for s in listed} == {"Second session"}


def test_create_session_defaults_to_a_name_when_none_is_given(
    auth_client: TestClient, project_id: str
) -> None:
    response = auth_client.post(sessions_url(project_id), json={})

    assert response.status_code == 201
    assert response.json()["name"] == "New session"


def test_create_session_rejects_a_blank_name(auth_client: TestClient, project_id: str) -> None:
    assert auth_client.post(sessions_url(project_id), json={"name": ""}).status_code == 422


def test_sessions_on_someone_elses_project_is_not_found(
    auth_client: TestClient, settings: Settings
) -> None:
    someone_elses = seed_project(settings, owner_username="other-user")

    assert auth_client.get(sessions_url(someone_elses.id)).status_code == 404
    assert auth_client.post(sessions_url(someone_elses.id), json={}).status_code == 404


def test_sessions_on_an_unknown_project_is_not_found(auth_client: TestClient) -> None:
    assert auth_client.get(sessions_url("no-such-project")).status_code == 404
