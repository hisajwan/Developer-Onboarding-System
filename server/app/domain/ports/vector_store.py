from typing import Protocol, runtime_checkable

from app.domain.models import ChunkRecord, RetrievedChunk


@runtime_checkable
class VectorStore(Protocol):
    async def existing_ids(self, ids: list[str]) -> set[str]:
        """Which of these chunk ids are already stored."""
        ...

    async def upsert(self, records: list[ChunkRecord]) -> None:
        """Insert new chunks, or overwrite ones with the same id."""
        ...

    async def remove_stale(self, source: str, keep_ids: set[str]) -> None:
        """Delete this source's chunks whose ids are not in `keep_ids` (from an older version)."""
        ...

    async def search(self, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]: ...

    async def count_documents(self) -> int:
        """Number of distinct sources that have at least one stored chunk."""
        ...
