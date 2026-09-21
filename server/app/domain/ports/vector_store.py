from typing import Protocol, runtime_checkable

from app.domain.models import Chunk, RetrievedChunk


@runtime_checkable
class VectorStore(Protocol):
    async def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None: ...

    async def search(self, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]: ...

    async def count_documents(self) -> int: ...
