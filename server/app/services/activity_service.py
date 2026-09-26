"""The Dashboard's numbers and history for one project, plus the shared wording of activity events.

Questions and reviews are recorded where they happen (the chat service and the Code review
screen's service); this service only reads them back and counts.
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from app.domain.models import ActivityEvent, ActivitySource, CodeReview, ProjectStats
from app.domain.ports import ActivityLog, DocumentRegistry
from app.review.diff import looks_like_diff, parse_diff

_TITLE_CHARS = 120
_DETAIL_CHARS = 200
_WEEK = timedelta(days=7)


def _shorten(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def question_event(project_id: str, question: str, answer: str, now: datetime) -> ActivityEvent:
    return ActivityEvent(
        project_id=project_id,
        kind="question",
        source="ask",
        title=_shorten(question, _TITLE_CHARS),
        detail=_shorten(answer, _DETAIL_CHARS),
        created_at=now,
    )


def review_event(
    project_id: str,
    code: str,
    summary: str,
    now: datetime,
    *,
    source: ActivitySource,
    review: CodeReview | None = None,
) -> ActivityEvent:
    return ActivityEvent(
        project_id=project_id,
        kind="review",
        source=source,
        title=_shorten(_review_title(code), _TITLE_CHARS),
        detail=_shorten(summary, _DETAIL_CHARS),
        created_at=now,
        finding_count=len(review.findings) if review is not None else None,
    )


def _review_title(code: str) -> str:
    """"Reviewed diff: <changed files>" for a diff, else "Reviewed: <first line of code>"."""
    # For code pasted into chat, label it by the code itself, not the words around it.
    if "```" in code:
        code = code.split("```", 1)[1].split("\n", 1)[-1]
    if looks_like_diff(code):
        files = [changed.path for changed in parse_diff(code)]
        return f"Reviewed diff: {', '.join(files) or 'no changed files'}"
    first_line = next(
        (line.strip() for line in code.splitlines() if line.strip() and line.strip() != "```"), ""
    )
    return f"Reviewed: {first_line}"


class ActivityService:
    def __init__(
        self,
        log: ActivityLog,
        documents: DocumentRegistry,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._log = log
        self._documents = documents
        self._clock = clock

    async def stats(self, project_id: str, recent_limit: int = 10) -> ProjectStats:
        week_ago = self._clock() - _WEEK
        return ProjectStats(
            questions_this_week=await self._log.count(project_id, "question", week_ago),
            reviews_this_week=await self._log.count(project_id, "review", week_ago),
            questions_total=await self._log.count(project_id, "question"),
            reviews_total=await self._log.count(project_id, "review"),
            documents_indexed=len(await self._documents.list_all(project_id)),
            recent=tuple(await self._log.recent(project_id, recent_limit)),
        )
