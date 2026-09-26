"""Code review from the Code review screen: the shared review, recorded as project activity."""

from collections.abc import Callable
from datetime import UTC, datetime

from app.domain.models import CodeReview, SnippetLanguage
from app.domain.ports import ActivityLog, CodeReviewer
from app.services.activity_service import review_event


class ProjectReviewService:
    def __init__(
        self,
        reviewer: CodeReviewer,
        activity: ActivityLog,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._reviewer = reviewer
        self._activity = activity
        self._clock = clock

    async def review(
        self, project_id: str, code: str, language: SnippetLanguage = "tsx"
    ) -> CodeReview:
        review = await self._reviewer.review(code, language)
        await self._activity.record(
            review_event(
                project_id, code, review.summary, self._clock(),
                source="code_review_screen", review=review,
            )
        )
        return review
