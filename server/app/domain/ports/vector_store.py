from typing import Protocol, runtime_checkable

from app.domain.models import ChunkRecord, RetrievedChunk


@runtime_checkable
class VectorStore(Protocol):
    """One shared store, scoped per call by `project_id` (a metadata filter, not a separate

    collection per project).
    """

    async def existing_ids(self, project_id: str, ids: list[str]) -> set[str]:
        """Which of these chunk ids are already stored for this project."""
        ...

    async def upsert(self, project_id: str, records: list[ChunkRecord]) -> None:
        """Insert new chunks, or overwrite ones with the same id."""
        ...

    async def remove_stale(self, project_id: str, source: str, keep_ids: set[str]) -> None:
        """Delete this source's chunks whose ids are not in `keep_ids` (from an older version)."""
        ...

    async def search(
        self, project_id: str, query_embedding: list[float], top_k: int
    ) -> list[RetrievedChunk]: ...

    async def count_documents(self, project_id: str) -> int:
        """Number of distinct sources in this project that have at least one stored chunk."""
        ...

    async def delete_project(self, project_id: str) -> None:
        """Removes every chunk of this project."""
        ...

    async def sources(self, project_id: str) -> list[str]:
        """The distinct sources (file names) in this project that have at least one chunk."""
        ...

    async def chunks_for_source(
        self, project_id: str, source: str, limit: int
    ) -> list[RetrievedChunk]:
        """Up to `limit` of one source's chunks, in document order (score 0: not a search hit)."""
        ...
