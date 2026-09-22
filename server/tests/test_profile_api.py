from fastapi.testclient import TestClient

from tests.conftest import PASSWORD, USERNAME


def test_profile_requires_login(client: TestClient) -> None:
    assert client.get("/api/v1/me").status_code == 401


def test_get_profile_returns_the_signed_in_users_details(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/me")

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == USERNAME
    assert body["first_name"] == "Dev"
    assert body["email"] == f"{USERNAME}@example.com"


def test_update_profile_changes_the_name(auth_client: TestClient) -> None:
    response = auth_client.patch("/api/v1/me", json={"first_name": "New", "last_name": "Name"})

    assert response.status_code == 200
    assert response.json()["first_name"] == "New"
    assert response.json()["last_name"] == "Name"
    assert auth_client.get("/api/v1/me").json()["first_name"] == "New"


def test_update_profile_cannot_change_username_or_email(auth_client: TestClient) -> None:
    response = auth_client.patch("/api/v1/me", json={"first_name": "New", "last_name": "Name"})

    assert response.json()["username"] == USERNAME
    assert response.json()["email"] == f"{USERNAME}@example.com"


def test_update_profile_rejects_a_blank_name(auth_client: TestClient) -> None:
    response = auth_client.patch("/api/v1/me", json={"first_name": "", "last_name": "Name"})

    assert response.status_code == 422


def test_change_password_with_the_correct_current_password(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/v1/me/change-password",
        json={"current_password": PASSWORD, "new_password": "a-new-password-1"},
    )

    assert response.status_code == 204


def test_login_works_with_the_new_password_after_a_change(auth_client: TestClient) -> None:
    auth_client.post(
        "/api/v1/me/change-password",
        json={"current_password": PASSWORD, "new_password": "a-new-password-1"},
    )
    auth_client.cookies.clear()

    response = auth_client.post(
        "/api/v1/login", json={"username": USERNAME, "password": "a-new-password-1"}
    )

    assert response.status_code == 200


def test_change_password_rejects_the_wrong_current_password(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/v1/me/change-password",
        json={"current_password": "totally-wrong", "new_password": "a-new-password-1"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_change_password_rejects_a_short_new_password(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/v1/me/change-password", json={"current_password": PASSWORD, "new_password": "short"}
    )

    assert response.status_code == 422
