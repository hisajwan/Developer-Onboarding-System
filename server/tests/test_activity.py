from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.domain.models import ActivityEvent, CodeReview, IndexedDocument, ReviewFinding
from app.domain.ports import ActivityLog
from app.infrastructure.storage.sqlite_activity_log import SqliteActivityLog
from app.services.activity_service import ActivityService, question_event, review_event
from app.services.project_review_service import ProjectReviewService
from tests.helpers import InMemoryRegistry

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


def event(kind: str, when: datetime, project_id: str = "p1", title: str = "t") -> ActivityEvent:
    return ActivityEvent(
        project_id=project_id, kind=kind, source="ask", title=title, detail="d", created_at=when
    )


@pytest.fixture
def log(tmp_path: Path) -> SqliteActivityLog:
    return SqliteActivityLog(tmp_path / "app.db")


def test_satisfies_the_activity_log_port(log: SqliteActivityLog) -> None:
    assert isinstance(log, ActivityLog)


@pytest.mark.anyio
async def test_recent_is_newest_first_and_per_project(log: SqliteActivityLog) -> None:
    await log.record(event("question", NOW, title="first"))
    await log.record(event("review", NOW, title="second"))
    await log.record(event("question", NOW, project_id="other", title="not mine"))

    assert [e.title for e in await log.recent("p1")] == ["second", "first"]


@pytest.mark.anyio
async def test_recent_respects_the_limit(log: SqliteActivityLog) -> None:
    for n in range(5):
        await log.record(event("question", NOW, title=str(n)))

    assert [e.title for e in await log.recent("p1", limit=2)] == ["4", "3"]


@pytest.mark.anyio
async def test_count_by_kind_and_since(log: SqliteActivityLog) -> None:
    await log.record(event("question", NOW - timedelta(days=10)))
    await log.record(event("question", NOW - timedelta(days=1)))
    await log.record(event("review", NOW))

    assert await log.count("p1", "question") == 2
    assert await log.count("p1", "question", since=NOW - timedelta(days=7)) == 1
    assert await log.count("p1", "review") == 1
    assert await log.count("other", "question") == 0


@pytest.mark.anyio
async def test_a_reviews_finding_count_round_trips(log: SqliteActivityLog) -> None:
    review = CodeReview(
        findings=(ReviewFinding("style", "m", "warning", "eslint"),) * 3,
        summary="Three issues.",
        judgement_available=True,
    )
    await log.record(review_event("p1", "const a = 1;", review.summary, NOW,
                                  source="code_review_screen", review=review))

    [saved] = await log.recent("p1")
    assert (saved.kind, saved.source, saved.finding_count) == ("review", "code_review_screen", 3)
    assert saved.created_at == NOW


@pytest.mark.parametrize(
    ("code", "title"),
    [
        ("const a = 1;\nconst b = 2;", "Reviewed: const a = 1;"),
        ("Please check:\n```tsx\n<img />\n```", "Reviewed: <img />"),
        (
            "diff --git a/src/A.tsx b/src/A.tsx\n--- a/src/A.tsx\n+++ b/src/A.tsx\n"
            "@@ -1,1 +1,2 @@\n x\n+y\n"
            "diff --git a/b.ts b/b.ts\n--- a/b.ts\n+++ b/b.ts\n@@ -1 +1 @@\n-a\n+b\n",
            "Reviewed diff: src/A.tsx, b.ts",
        ),
    ],
)
def test_a_review_is_titled_by_its_code_or_its_changed_files(code: str, title: str) -> None:
    assert review_event("p1", code, "s", NOW, source="ask").title == title


def test_long_questions_are_shortened_to_one_line() -> None:
    made = question_event("p1", "How\ndo I " + "x" * 300, "answer", NOW)

    assert "\n" not in made.title
    assert len(made.title) <= 120 and made.title.endswith("…")


@pytest.mark.anyio
async def test_stats_combine_this_week_totals_documents_and_recent(log: SqliteActivityLog) -> None:
    documents = InMemoryRegistry()
    for name in ("a.md", "b.pdf"):
        await documents.record(
            "p1", IndexedDocument(name, "hash", "sig", chunk_count=1, indexed_at=NOW)
        )
    await log.record(event("question", NOW - timedelta(days=30)))
    await log.record(event("question", NOW - timedelta(hours=1), title="latest question"))
    await log.record(event("review", NOW - timedelta(days=2), title="a review"))
    service = ActivityService(log, documents, clock=lambda: NOW)

    stats = await service.stats("p1")

    assert (stats.questions_this_week, stats.questions_total) == (1, 2)
    assert (stats.reviews_this_week, stats.reviews_total) == (1, 1)
    assert stats.documents_indexed == 2
    assert [e.title for e in stats.recent][:2] == ["a review", "latest question"]


class FixedReviewer:
    async def review(self, code: str, language: str = "tsx") -> CodeReview:
        return CodeReview(findings=(), summary="Looks good.", judgement_available=True)


@pytest.mark.anyio
async def test_a_screen_review_is_returned_and_recorded(log: SqliteActivityLog) -> None:
    service = ProjectReviewService(FixedReviewer(), log, clock=lambda: NOW)

    review = await service.review("p1", "export const A = () => null;")

    assert review.summary == "Looks good."
    [saved] = await log.recent("p1")
    assert (saved.title, saved.detail, saved.finding_count) == (
        "Reviewed: export const A = () => null;", "Looks good.", 0
    )
