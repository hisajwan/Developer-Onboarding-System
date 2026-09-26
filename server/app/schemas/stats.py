from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.domain.models import ActivityEvent, ProjectStats


class ActivityResponse(BaseModel):
    kind: Literal["question", "review"]
    source: Literal["ask", "code_review_screen"]
    title: str
    detail: str
    finding_count: int | None
    created_at: datetime

    @classmethod
    def from_domain(cls, event: ActivityEvent) -> "ActivityResponse":
        return cls(
            kind=event.kind,
            source=event.source,
            title=event.title,
            detail=event.detail,
            finding_count=event.finding_count,
            created_at=event.created_at,
        )


class StatsResponse(BaseModel):
    questions_this_week: int
    reviews_this_week: int
    questions_total: int
    reviews_total: int
    documents_indexed: int
    recent: list[ActivityResponse]

    @classmethod
    def from_domain(cls, stats: ProjectStats) -> "StatsResponse":
        return cls(
            questions_this_week=stats.questions_this_week,
            reviews_this_week=stats.reviews_this_week,
            questions_total=stats.questions_total,
            reviews_total=stats.reviews_total,
            documents_indexed=stats.documents_indexed,
            recent=[ActivityResponse.from_domain(event) for event in stats.recent],
        )
