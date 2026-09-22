from fastapi.testclient import TestClient

GUIDE = b"# Dev setup\n\nRun npm install, then start the app with npm run dev."


def upload(client: TestClient, name: str, content: bytes) -> None:
    response = client.post(
        "/api/v1/documents", files={"file": (name, content, "text/markdown")}
    )
    assert response.status_code == 200


def ask(client: TestClient, message: str):
    return client.post("/api/v1/chat", json={"message": message})


def test_chat_rejects_an_empty_message(auth_client: TestClient) -> None:
    assert ask(auth_client, "").status_code == 422


def test_a_question_with_no_documents_indexed_gets_an_honest_answer(
    auth_client: TestClient,
) -> None:
    response = ask(auth_client, "How do I set up the dev environment?")

    body = response.json()
    assert response.status_code == 200
    assert "couldn't find" in body["reply"]
    assert body["sources"] == []
    assert body["tools_used"] == ["retrieve_and_answer"]


def test_a_question_about_an_indexed_doc_is_grounded_and_cites_it(
    auth_client: TestClient,
) -> None:
    upload(auth_client, "dev-setup.md", GUIDE)

    response = ask(auth_client, "How do I set up the dev environment?")

    body = response.json()
    assert response.status_code == 200
    assert "npm install" in body["reply"]
    assert body["sources"] == ["dev-setup.md"]
    assert body["tools_used"] == ["retrieve_and_answer"]
