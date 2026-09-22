from typing import Protocol, runtime_checkable

from app.domain.models import IndexedDocument


@runtime_checkable
class DocumentRegistry(Protocol):
    """Records which documents are indexed and how, so an unchanged re-upload can be skipped."""

    async def get(self, filename: str) -> IndexedDocument | None: ...

    async def record(self, document: IndexedDocument) -> None:
        """Insert, or replace the entry with the same filename."""
        ...

    async def list_all(self) -> list[IndexedDocument]: ...
