from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api.session_cookie import SESSION_COOKIE
from app.core.config import Settings
from app.infrastructure.auth.jwt_tokens import JwtSessionTokens
from app.main import create_app
from tests.conftest import PASSWORD, SECRET, USERNAME, seed_user


def login(client: TestClient, username: str = USERNAME, password: str = PASSWORD):
    return client.post("/api/v1/login", json={"username": username, "password": password})


def signup(client: TestClient, **overrides):
    body = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "username": "ada",
        "password": "s3cret-pass",
        **overrides,
    }
    return client.post("/api/v1/signup", json=body)


def error_code(response) -> str:
    return response.json()["error"]["code"]


def test_protected_endpoint_requires_login(client: TestClient) -> None:
    response = client.get("/api/v1/projects")

    assert response.status_code == 401
    assert error_code(response) == "not_authenticated"


def test_health_stays_public(client: TestClient) -> None:
    assert client.get("/api/v1/health").status_code == 200


def test_login_sets_an_httponly_session_cookie_and_keeps_the_token_out_of_the_body(
    client: TestClient,
) -> None:
    response = login(client)

    assert response.status_code == 200
    assert response.json() == {"username": USERNAME, "last_project_id": None}
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"{SESSION_COOKIE}=")
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert client.cookies[SESSION_COOKIE] not in response.text


def test_signup_creates_an_account_and_logs_it_in(client: TestClient) -> None:
    response = signup(client)

    assert response.status_code == 201
    assert response.json() == {"username": "ada", "last_project_id": None}
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"{SESSION_COOKIE}=")
    assert "HttpOnly" in cookie

    assert client.get("/api/v1/session").json() == {"username": "ada", "last_project_id": None}


def test_signup_then_login_with_the_new_password_works(client: TestClient) -> None:
    signup(client)
    client.cookies.clear()

    response = login(client, username="ada", password="s3cret-pass")

    assert response.status_code == 200


def test_signup_rejects_a_username_that_is_already_taken(client: TestClient) -> None:
    response = signup(client, username=USERNAME, email="someone-else@example.com")

    assert response.status_code == 409
    assert error_code(response) == "account_already_exists"


def test_signup_rejects_an_email_that_is_already_registered(client: TestClient) -> None:
    signup(client)

    response = signup(client, username="someone-else")

    assert response.status_code == 409
    assert error_code(response) == "account_already_exists"


def test_signup_rejects_a_short_password(client: TestClient) -> None:
    assert signup(client, password="short").status_code == 422


def test_signup_rejects_a_malformed_email(client: TestClient) -> None:
    assert signup(client, email="not-an-email").status_code == 422


def test_signup_rejects_a_blank_name(client: TestClient) -> None:
    assert signup(client, first_name="").status_code == 422


def test_logged_in_client_can_use_protected_endpoints(
    auth_client: TestClient, project_id: str, chat_session_id: str
) -> None:
    url = f"/api/v1/projects/{project_id}/sessions/{chat_session_id}/chat"
    response = auth_client.post(url, json={"message": "hello"})
    assert response.status_code == 200


def test_session_endpoint_reports_the_user_only_when_logged_in(client: TestClient) -> None:
    assert client.get("/api/v1/session").status_code == 401

    login(client)

    assert client.get("/api/v1/session").json() == {"username": USERNAME, "last_project_id": None}


def test_wrong_password_is_rejected_without_a_cookie(client: TestClient) -> None:
    response = login(client, password="nope")

    assert response.status_code == 401
    assert error_code(response) == "invalid_credentials"
    assert "set-cookie" not in response.headers


def test_wrong_username_gets_the_same_answer_as_a_wrong_password(client: TestClient) -> None:
    wrong_user = login(client, username="someone-else")
    wrong_password = login(client, password="nope")

    assert wrong_user.status_code == wrong_password.status_code == 401
    assert wrong_user.json() == wrong_password.json()


def test_logout_ends_the_session(
    auth_client: TestClient, project_id: str, chat_session_id: str
) -> None:
    assert auth_client.post("/api/v1/logout").status_code == 204

    url = f"/api/v1/projects/{project_id}/sessions/{chat_session_id}/chat"
    response = auth_client.post(url, json={"message": "hello"})
    assert response.status_code == 401


def test_empty_credentials_are_a_validation_error(client: TestClient) -> None:
    assert login(client, username="", password="").status_code == 422


def test_a_garbage_cookie_is_rejected(client: TestClient) -> None:
    client.cookies.set(SESSION_COOKIE, "not-a-token")

    assert client.get("/api/v1/session").status_code == 401


def test_a_token_signed_with_another_secret_is_rejected(client: TestClient) -> None:
    forged = JwtSessionTokens(SecretStr("x" * 40), timedelta(minutes=5)).issue(USERNAME)
    client.cookies.set(SESSION_COOKIE, forged)

    assert client.get("/api/v1/session").status_code == 401


def test_an_expired_token_is_rejected(client: TestClient) -> None:
    expired = JwtSessionTokens(SecretStr(SECRET), timedelta(seconds=-1)).issue(USERNAME)
    client.cookies.set(SESSION_COOKIE, expired)

    assert client.get("/api/v1/session").status_code == 401


def test_login_reports_missing_configuration_instead_of_letting_anyone_in() -> None:
    unconfigured = TestClient(create_app(Settings(environment="test", _env_file=None)))

    response = login(unconfigured)

    assert response.status_code == 500
    assert error_code(response) == "configuration_error"
    assert unconfigured.get("/api/v1/projects").status_code == 500


def test_a_blank_signing_secret_is_treated_as_not_configured(tmp_path: Path) -> None:
    """AUTH_SECRET= in .env is present but blank, not absent; the app must still refuse to start

    login rather than sign tokens with an empty, guessable secret.
    """
    settings = Settings(
        environment="test", data_dir=tmp_path / "data", auth_secret=SecretStr("   "), _env_file=None
    )
    seed_user(settings)
    blank = TestClient(create_app(settings))

    response = login(blank)

    assert response.status_code == 500
    assert error_code(response) == "configuration_error"


def test_cookie_is_secure_in_production(tmp_path: Path) -> None:
    settings = Settings(
        environment="production",
        data_dir=tmp_path / "data",
        auth_secret=SecretStr(SECRET),
        _env_file=None,
    )
    seed_user(settings)

    response = login(TestClient(create_app(settings), base_url="https://testserver"))

    assert "Secure" in response.headers["set-cookie"]
