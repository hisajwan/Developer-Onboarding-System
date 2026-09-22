from fastapi.testclient import TestClient

from app.core.config import Settings
from tests.conftest import seed_project

GUIDE = b"# Dev setup\n\nRun npm install, then start the app with npm run dev."


def upload(client: TestClient, project_id: str, name: str, content: bytes) -> None:
    response = client.post(
        f"/api/v1/projects/{project_id}/documents", files={"file": (name, content, "text/markdown")}
    )
    assert response.status_code == 200


def ask(client: TestClient, project_id: str, message: str):
    return client.post(f"/api/v1/projects/{project_id}/chat", json={"message": message})


def test_chat_rejects_an_empty_message(auth_client: TestClient, project_id: str) -> None:
    assert ask(auth_client, project_id, "").status_code == 422


def test_a_question_with_no_documents_indexed_gets_an_honest_answer(
    auth_client: TestClient, project_id: str
) -> None:
    response = ask(auth_client, project_id, "How do I set up the dev environment?")

    body = response.json()
    assert response.status_code == 200
    assert "couldn't find" in body["reply"]
    assert body["sources"] == []
    assert body["tools_used"] == ["retrieve_and_answer"]


def test_a_question_about_an_indexed_doc_is_grounded_and_cites_it(
    auth_client: TestClient, project_id: str
) -> None:
    upload(auth_client, project_id, "dev-setup.md", GUIDE)

    response = ask(auth_client, project_id, "How do I set up the dev environment?")

    body = response.json()
    assert response.status_code == 200
    assert "npm install" in body["reply"]
    assert body["sources"] == ["dev-setup.md"]
    assert body["tools_used"] == ["retrieve_and_answer"]


def test_a_question_about_a_document_in_another_project_gets_no_match(
    auth_client: TestClient, project_id: str, settings: Settings
) -> None:
    """Retrieval is scoped per project: a document indexed in one project is invisible to another,

    even for the same user.
    """
    upload(auth_client, project_id, "dev-setup.md", GUIDE)
    other_project = seed_project(settings, name="Another Project")

    response = ask(auth_client, other_project.id, "How do I set up the dev environment?")

    assert response.status_code == 200
    assert "couldn't find" in response.json()["reply"]


def test_chat_history_round_trips_through_the_api(auth_client: TestClient, project_id: str) -> None:
    assert ask(auth_client, project_id, "How do I set up the dev environment?").status_code == 200

    history = auth_client.get(f"/api/v1/projects/{project_id}/chat/history").json()["messages"]

    assert [m["role"] for m in history] == ["user", "assistant"]
    assert history[0]["content"] == "How do I set up the dev environment?"


def test_chat_history_is_scoped_per_project(
    auth_client: TestClient, project_id: str, settings: Settings
) -> None:
    ask(auth_client, project_id, "How do I set up the dev environment?")
    other_project = seed_project(settings, name="Another Project")

    response = auth_client.get(f"/api/v1/projects/{other_project.id}/chat/history")

    assert response.json()["messages"] == []


def test_chat_on_someone_elses_project_is_not_found(
    auth_client: TestClient, settings: Settings
) -> None:
    someone_elses = seed_project(settings, owner_username="other-user")

    response = ask(auth_client, someone_elses.id, "hello")

    assert response.status_code == 404


def test_chat_on_an_unknown_project_is_not_found(auth_client: TestClient) -> None:
    assert ask(auth_client, "no-such-project", "hello").status_code == 404
