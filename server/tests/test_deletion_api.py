"""Deleting sessions, projects and the account through the API, against the real stores."""

import asyncio
import sqlite3
from contextlib import closing

from fastapi.testclient import TestClient

from app.core.config import Settings
from tests.conftest import PASSWORD, USERNAME, seed_project

GUIDE = b"# Dev setup\n\nInstall dependencies with npm install, then start with npm run dev."


def rows(settings: Settings, table: str) -> int:
    with closing(sqlite3.connect(settings.database_path)) as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def chunks(client: TestClient, project_id: str) -> int:
    vectors = client.app.state.container.vector_store
    return asyncio.run(vectors.count_documents(project_id))


def new_project_with_content(client: TestClient, name: str = "Doomed") -> str:
    """A project with its Session 1, one chat message pair, one document and activity."""
    project_id = client.post("/api/v1/projects", json={"name": name}).json()["id"]
    upload = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("guide.md", GUIDE, "text/markdown")},
    )
    assert upload.status_code == 200
    [session] = client.get(f"/api/v1/projects/{project_id}/sessions").json()["sessions"]
    chat = client.post(
        f"/api/v1/projects/{project_id}/sessions/{session['id']}/chat",
        json={"message": "How do I start?"},
    )
    assert chat.status_code == 200
    return project_id


# --- sessions ---------------------------------------------------------------------------------


def test_deleting_a_session_removes_it_and_its_messages(
    auth_client: TestClient, settings: Settings
) -> None:
    project_id = new_project_with_content(auth_client)
    [session] = auth_client.get(f"/api/v1/projects/{project_id}/sessions").json()["sessions"]
    assert rows(settings, "chat_messages") == 2

    response = auth_client.delete(f"/api/v1/projects/{project_id}/sessions/{session['id']}")

    assert response.status_code == 204
    [fresh] = auth_client.get(f"/api/v1/projects/{project_id}/sessions").json()["sessions"]
    assert fresh["name"] == "Session 1" and fresh["id"] != session["id"]
    assert rows(settings, "chat_messages") == 0


def test_an_unknown_session_is_a_404(auth_client: TestClient, project_id: str) -> None:
    response = auth_client.delete(f"/api/v1/projects/{project_id}/sessions/nope")

    assert response.status_code == 404


# --- projects ---------------------------------------------------------------------------------


def test_deleting_a_project_removes_its_rows_chunks_and_files(
    auth_client: TestClient, settings: Settings
) -> None:
    project_id = new_project_with_content(auth_client)
    assert chunks(auth_client, project_id) == 1
    assert (settings.docs_dir / project_id / "guide.md").is_file()

    response = auth_client.delete(f"/api/v1/projects/{project_id}")

    assert response.status_code == 204
    ids = [p["id"] for p in auth_client.get("/api/v1/projects").json()["projects"]]
    assert project_id not in ids
    assert chunks(auth_client, project_id) == 0
    assert not (settings.docs_dir / project_id).exists()
    for table in ("documents", "chat_messages", "activity"):
        assert rows(settings, table) == 0, table


def test_deleting_one_project_leaves_the_others_alone(
    auth_client: TestClient, project_id: str
) -> None:
    doomed = new_project_with_content(auth_client)
    kept = new_project_with_content(auth_client, "Kept")

    auth_client.delete(f"/api/v1/projects/{doomed}")

    assert chunks(auth_client, kept) == 1
    assert len(auth_client.get(f"/api/v1/projects/{kept}/documents").json()["documents"]) == 1


def test_someone_elses_project_cannot_be_deleted(
    auth_client: TestClient, settings: Settings
) -> None:
    other = seed_project(settings, owner_username="someone-else")

    assert auth_client.delete(f"/api/v1/projects/{other.id}").status_code == 404
    assert rows(settings, "projects") == 2  # the fixture's project and theirs


def test_deleting_the_last_selected_project_forgets_it(auth_client: TestClient) -> None:
    project_id = new_project_with_content(auth_client)
    auth_client.post(f"/api/v1/projects/{project_id}/select")

    auth_client.delete(f"/api/v1/projects/{project_id}")

    assert auth_client.get("/api/v1/session").json()["last_project_id"] is None


# --- account ----------------------------------------------------------------------------------


def delete_account(client: TestClient, password: str):
    return client.request("DELETE", "/api/v1/me", json={"password": password})


def test_the_wrong_password_does_not_delete_the_account(auth_client: TestClient) -> None:
    response = delete_account(auth_client, "wrong-password")

    assert response.status_code == 401
    assert auth_client.get("/api/v1/me").status_code == 200


def test_deleting_the_account_removes_everything_and_logs_out(
    auth_client: TestClient, settings: Settings
) -> None:
    project_id = new_project_with_content(auth_client)

    response = delete_account(auth_client, PASSWORD)

    assert response.status_code == 204
    assert auth_client.get("/api/v1/me").status_code == 401  # cookie cleared
    for table in ("users", "projects", "chat_sessions", "chat_messages", "documents", "activity"):
        assert rows(settings, table) == 0, table
    assert chunks(auth_client, project_id) == 0
    assert not (settings.docs_dir / project_id).exists()
    login = auth_client.post(
        "/api/v1/login", json={"username": USERNAME, "password": PASSWORD}
    )
    assert login.status_code == 401
