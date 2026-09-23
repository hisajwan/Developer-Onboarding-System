from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from tests.conftest import requires_linter, seed_project

FLAWED = "function Card({ src }) {\n  return <img src={src} />;\n}"


def review(client: TestClient, project_id: str, **body):
    return client.post(f"/api/v1/projects/{project_id}/reviews", json=body)


def test_reviewing_requires_a_login(client: TestClient, project_id: str) -> None:
    assert review(client, project_id, code=FLAWED).status_code == 401


def test_empty_code_is_rejected(auth_client: TestClient, project_id: str) -> None:
    assert review(auth_client, project_id, code="").status_code == 422


def test_an_unknown_language_is_rejected(auth_client: TestClient, project_id: str) -> None:
    assert review(auth_client, project_id, code=FLAWED, language="python").status_code == 422


def test_someone_elses_project_is_a_404(auth_client: TestClient, settings: Settings) -> None:
    other = seed_project(settings, owner_username="someone-else")
    assert review(auth_client, other.id, code=FLAWED).status_code == 404


def test_a_missing_linter_install_is_a_clear_configuration_error(
    make_client, project_id: str, tmp_path: Path
) -> None:
    client = make_client(lint_dir=tmp_path / "not-installed")

    response = review(client, project_id, code=FLAWED)

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "configuration_error"
    assert "npm install" in response.json()["error"]["message"]


@requires_linter
def test_a_flawed_snippet_gets_categorised_eslint_findings(
    auth_client: TestClient, project_id: str
) -> None:
    response = review(auth_client, project_id, code=FLAWED)

    body = response.json()
    assert response.status_code == 200
    alt = next(f for f in body["findings"] if f["rule_id"] == "jsx-a11y/alt-text")
    assert alt == {
        "category": "accessibility",
        "message": alt["message"],
        "severity": "error",
        "source": "eslint",
        "line": 2,
        "rule_id": "jsx-a11y/alt-text",
    }
    # The fake LLM's echo is not review JSON, so the review says the model part is missing.
    assert body["judgement_available"] is False
    assert body["parse_error"] is None


@requires_linter
def test_a_clean_snippet_gets_no_invented_findings(
    auth_client: TestClient, project_id: str
) -> None:
    code = "export function Title({ text }: { text: string }) {\n  return <h1>{text}</h1>;\n}"

    body = review(auth_client, project_id, code=code).json()

    assert body["findings"] == []
    assert "no issues" in body["summary"]


@requires_linter
def test_a_snippet_that_does_not_parse_says_so(auth_client: TestClient, project_id: str) -> None:
    body = review(auth_client, project_id, code="const = ;", language="ts").json()

    assert body["findings"] == []
    assert "Parsing error" in body["parse_error"]
