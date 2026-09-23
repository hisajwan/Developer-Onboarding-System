from fastapi.testclient import TestClient

from app.core.config import Settings
from tests.conftest import PROJECT_NAME, seed_project


def test_projects_require_login(client: TestClient) -> None:
    assert client.get("/api/v1/projects").status_code == 401
    assert client.post("/api/v1/projects", json={"name": "x"}).status_code == 401


def test_list_projects_includes_the_seeded_project(
    auth_client: TestClient, project_id: str
) -> None:
    listed = auth_client.get("/api/v1/projects").json()["projects"]

    assert [p["id"] for p in listed] == [project_id]
    assert listed[0]["name"] == PROJECT_NAME


def test_create_project_and_see_it_listed(auth_client: TestClient) -> None:
    response = auth_client.post("/api/v1/projects", json={"name": "New Project"})

    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "New Project"

    listed = auth_client.get("/api/v1/projects").json()["projects"]
    assert created["id"] in [p["id"] for p in listed]


def test_create_project_rejects_a_blank_name(auth_client: TestClient) -> None:
    assert auth_client.post("/api/v1/projects", json={"name": ""}).status_code == 422


def test_list_projects_never_shows_someone_elses(
    auth_client: TestClient, settings: Settings
) -> None:
    seed_project(settings, owner_username="other-user", name="Not Yours")

    listed = auth_client.get("/api/v1/projects").json()["projects"]

    assert "Not Yours" not in [p["name"] for p in listed]


def test_rename_project(auth_client: TestClient, project_id: str) -> None:
    response = auth_client.patch(f"/api/v1/projects/{project_id}", json={"name": "Renamed"})

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"
    assert auth_client.get("/api/v1/projects").json()["projects"][0]["name"] == "Renamed"


def test_rename_someone_elses_project_is_not_found(
    auth_client: TestClient, settings: Settings
) -> None:
    someone_elses = seed_project(settings, owner_username="other-user")

    response = auth_client.patch(f"/api/v1/projects/{someone_elses.id}", json={"name": "Stolen"})

    assert response.status_code == 404


def test_rename_an_unknown_project_is_not_found(auth_client: TestClient) -> None:
    response = auth_client.patch("/api/v1/projects/no-such-project", json={"name": "x"})

    assert response.status_code == 404


def test_select_project_sets_it_as_the_last_project_in_the_session(
    auth_client: TestClient, project_id: str
) -> None:
    select = auth_client.post(f"/api/v1/projects/{project_id}/select")
    assert select.status_code == 200

    session = auth_client.get("/api/v1/session").json()
    assert session["last_project_id"] == project_id


def test_select_someone_elses_project_is_not_found(
    auth_client: TestClient, settings: Settings
) -> None:
    someone_elses = seed_project(settings, owner_username="other-user")

    response = auth_client.post(f"/api/v1/projects/{someone_elses.id}/select")

    assert response.status_code == 404
