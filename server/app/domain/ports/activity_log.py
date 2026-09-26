from datetime import datetime
from typing import Protocol, runtime_checkable

from app.domain.models import ActivityEvent, ActivityKind


@runtime_checkable
class ActivityLog(Protocol):
    """A project's history of questions and reviews."""

    async def record(self, event: ActivityEvent) -> None: ...

    async def recent(self, project_id: str, limit: int = 10) -> list[ActivityEvent]:
        """Newest first."""
        ...

    async def count(
        self, project_id: str, kind: ActivityKind, since: datetime | None = None
    ) -> int: ...
