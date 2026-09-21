from fastapi.testclient import TestClient


def test_health_reports_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["environment"] == "test"


def test_cors_allows_the_frontend_origin(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_chat_returns_a_reply(auth_client: TestClient) -> None:
    response = auth_client.post("/api/v1/chat", json={"message": "hello"})

    assert response.status_code == 200
    assert "Agent not wired yet" in response.json()["reply"]


def test_chat_rejects_an_empty_message(auth_client: TestClient) -> None:
    response = auth_client.post("/api/v1/chat", json={"message": ""})

    assert response.status_code == 422
