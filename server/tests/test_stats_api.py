from fastapi.testclient import TestClient

from app.core.config import Settings
from tests.conftest import requires_linter, seed_project


def stats(client: TestClient, project_id: str):
    return client.get(f"/api/v1/projects/{project_id}/stats")


def test_stats_require_a_login(client: TestClient, project_id: str) -> None:
    assert stats(client, project_id).status_code == 401


def test_someone_elses_project_is_a_404(auth_client: TestClient, settings: Settings) -> None:
    other = seed_project(settings, owner_username="someone-else")
    assert stats(auth_client, other.id).status_code == 404


def test_a_new_project_has_zero_counts(auth_client: TestClient, project_id: str) -> None:
    body = stats(auth_client, project_id).json()

    assert body == {
        "questions_this_week": 0,
        "reviews_this_week": 0,
        "questions_total": 0,
        "reviews_total": 0,
        "documents_indexed": 0,
        "recent": [],
    }


def test_questions_and_documents_are_counted(
    auth_client: TestClient, project_id: str, chat_session_id: str
) -> None:
    auth_client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("setup.md", b"# Setup\n\nRun npm install.", "text/markdown")},
    )
    auth_client.post(
        f"/api/v1/projects/{project_id}/sessions/{chat_session_id}/chat",
        json={"message": "How do I set up?"},
    )

    body = stats(auth_client, project_id).json()

    assert (body["questions_this_week"], body["questions_total"]) == (1, 1)
    assert body["documents_indexed"] == 1
    [latest] = body["recent"]
    assert (latest["kind"], latest["source"], latest["title"]) == ("question", "ask",
                                                                    "How do I set up?")


@requires_linter
def test_a_screen_review_is_counted_with_its_findings(
    auth_client: TestClient, project_id: str
) -> None:
    auth_client.post(
        f"/api/v1/projects/{project_id}/reviews",
        json={"code": "function Card({ src }) {\n  return <img src={src} />;\n}"},
    )

    body = stats(auth_client, project_id).json()

    assert (body["reviews_this_week"], body["reviews_total"]) == (1, 1)
    [latest] = body["recent"]
    assert latest["source"] == "code_review_screen"
    assert latest["title"] == "Reviewed: function Card({ src }) {"
    assert latest["finding_count"] >= 1


def test_activity_stays_in_its_own_project(
    auth_client: TestClient, project_id: str, chat_session_id: str, settings: Settings
) -> None:
    auth_client.post(
        f"/api/v1/projects/{project_id}/sessions/{chat_session_id}/chat",
        json={"message": "a question"},
    )
    mine_too = seed_project(settings, name="Second")

    assert stats(auth_client, mine_too.id).json()["questions_total"] == 0
