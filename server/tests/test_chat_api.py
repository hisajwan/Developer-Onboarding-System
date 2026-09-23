from fastapi.testclient import TestClient

from app.core.config import Settings
from tests.conftest import seed_chat_session, seed_project

GUIDE = b"# Dev setup\n\nRun npm install, then start the app with npm run dev."


def upload(client: TestClient, project_id: str, name: str, content: bytes) -> None:
    response = client.post(
        f"/api/v1/projects/{project_id}/documents", files={"file": (name, content, "text/markdown")}
    )
    assert response.status_code == 200


def ask(client: TestClient, project_id: str, session_id: str, message: str):
    url = f"/api/v1/projects/{project_id}/sessions/{session_id}/chat"
    return client.post(url, json={"message": message})


def history_url(project_id: str, session_id: str) -> str:
    return f"/api/v1/projects/{project_id}/sessions/{session_id}/chat/history"


def test_chat_rejects_an_empty_message(
    auth_client: TestClient, project_id: str, chat_session_id: str
) -> None:
    assert ask(auth_client, project_id, chat_session_id, "").status_code == 422


def test_a_question_with_no_documents_indexed_gets_an_honest_answer(
    auth_client: TestClient, project_id: str, chat_session_id: str
) -> None:
    response = ask(auth_client, project_id, chat_session_id, "How do I set up the dev environment?")

    body = response.json()
    assert response.status_code == 200
    assert "couldn't find" in body["reply"]
    assert body["sources"] == []
    assert body["tools_used"] == ["retrieve_and_answer"]


def test_a_question_about_an_indexed_doc_is_grounded_and_cites_it(
    auth_client: TestClient, project_id: str, chat_session_id: str
) -> None:
    upload(auth_client, project_id, "dev-setup.md", GUIDE)

    response = ask(auth_client, project_id, chat_session_id, "How do I set up the dev environment?")

    body = response.json()
    assert response.status_code == 200
    assert "npm install" in body["reply"]
    assert body["sources"] == ["dev-setup.md"]
    assert body["tools_used"] == ["retrieve_and_answer"]


def test_a_question_about_a_document_in_another_project_gets_no_match(
    auth_client: TestClient, project_id: str, chat_session_id: str, settings: Settings
) -> None:
    """Retrieval is scoped per project: a document indexed in one project is invisible to another,

    even for the same user.
    """
    upload(auth_client, project_id, "dev-setup.md", GUIDE)
    other_project = seed_project(settings, name="Another Project")
    other_session = seed_chat_session(settings, other_project.id)

    response = ask(
        auth_client, other_project.id, other_session.id, "How do I set up the dev environment?"
    )

    assert response.status_code == 200
    assert "couldn't find" in response.json()["reply"]


def test_chat_history_round_trips_through_the_api(
    auth_client: TestClient, project_id: str, chat_session_id: str
) -> None:
    question = "How do I set up the dev environment?"
    assert ask(auth_client, project_id, chat_session_id, question).status_code == 200

    history = auth_client.get(history_url(project_id, chat_session_id)).json()["messages"]

    assert [m["role"] for m in history] == ["user", "assistant"]
    assert history[0]["content"] == question


def test_chat_history_is_scoped_per_session(
    auth_client: TestClient, project_id: str, chat_session_id: str, settings: Settings
) -> None:
    ask(auth_client, project_id, chat_session_id, "How do I set up the dev environment?")
    other_session = seed_chat_session(settings, project_id, name="Second session")

    response = auth_client.get(history_url(project_id, other_session.id))

    assert response.json()["messages"] == []


def test_chat_on_someone_elses_project_is_not_found(
    auth_client: TestClient, settings: Settings
) -> None:
    someone_elses = seed_project(settings, owner_username="other-user")
    their_session = seed_chat_session(settings, someone_elses.id)

    response = ask(auth_client, someone_elses.id, their_session.id, "hello")

    assert response.status_code == 404


def test_chat_on_an_unknown_project_is_not_found(auth_client: TestClient) -> None:
    assert ask(auth_client, "no-such-project", "no-such-session", "hello").status_code == 404


def test_chat_on_an_unknown_session_is_not_found(
    auth_client: TestClient, project_id: str
) -> None:
    assert ask(auth_client, project_id, "no-such-session", "hello").status_code == 404


def test_chat_on_a_session_from_a_different_project_is_not_found(
    auth_client: TestClient, project_id: str, settings: Settings
) -> None:
    """A session id is only valid nested under the project it actually belongs to."""
    other_project = seed_project(settings, name="Another Project")
    session_of_other_project = seed_chat_session(settings, other_project.id)

    response = ask(auth_client, project_id, session_of_other_project.id, "hello")

    assert response.status_code == 404
