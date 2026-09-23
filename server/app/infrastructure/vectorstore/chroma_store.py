"""Chroma-backed vector store. Persistent on disk, so chunks survive a backend restart.

One shared collection: every chunk is tagged with a `project_id` in its metadata, and every
query/delete filters on it. This keeps retrieval scoped per project without a collection per
project.
"""

import asyncio
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.domain.models import Chunk, ChunkRecord, RetrievedChunk


def _to_metadata(project_id: str, chunk: Chunk) -> dict:
    # Chroma metadata values cannot be None, so "page" is only present when the chunk has one.
    metadata = {
        "project_id": project_id,
        "source": chunk.source,
        "index": chunk.index,
        "is_image_caption": chunk.is_image_caption,
    }
    if chunk.page is not None:
        metadata["page"] = chunk.page
    return metadata


def _from_metadata(text: str, metadata: dict) -> Chunk:
    return Chunk(
        text=text,
        source=metadata["source"],
        index=metadata["index"],
        is_image_caption=metadata["is_image_caption"],
        page=metadata.get("page"),
    )


class ChromaVectorStore:
    def __init__(self, path: Path, collection_name: str = "documents") -> None:
        path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(
            path=str(path), settings=ChromaSettings(anonymized_telemetry=False)
        )
        # Embeddings always come from our Embedder, so Chroma's own embedding function is off.
        self._collection = client.get_or_create_collection(
            collection_name,
            configuration={"hnsw": {"space": "cosine"}},
            embedding_function=None,
        )

    async def existing_ids(self, project_id: str, ids: list[str]) -> set[str]:
        if not ids:
            return set()
        found = await asyncio.to_thread(
            self._collection.get, ids=ids, where={"project_id": project_id}, include=[]
        )
        return set(found["ids"])

    async def upsert(self, project_id: str, records: list[ChunkRecord]) -> None:
        if not records:
            return
        await asyncio.to_thread(
            self._collection.upsert,
            ids=[record.id for record in records],
            embeddings=[record.embedding for record in records],
            documents=[record.chunk.text for record in records],
            metadatas=[_to_metadata(project_id, record.chunk) for record in records],
        )

    async def remove_stale(self, project_id: str, source: str, keep_ids: set[str]) -> None:
        stored = await asyncio.to_thread(
            self._collection.get,
            where={"$and": [{"project_id": project_id}, {"source": source}]},
            include=[],
        )
        stale = [chunk_id for chunk_id in stored["ids"] if chunk_id not in keep_ids]
        if stale:
            await asyncio.to_thread(self._collection.delete, ids=stale)

    async def search(
        self, project_id: str, query_embedding: list[float], top_k: int
    ) -> list[RetrievedChunk]:
        result = await asyncio.to_thread(
            self._collection.query,
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"project_id": project_id},
            include=["documents", "metadatas", "distances"],
        )
        return [
            RetrievedChunk(chunk=_from_metadata(text, metadata), score=1.0 - distance)
            for text, metadata, distance in zip(
                result["documents"][0], result["metadatas"][0], result["distances"][0], strict=True
            )
        ]

    async def count_documents(self, project_id: str) -> int:
        stored = await asyncio.to_thread(
            self._collection.get, where={"project_id": project_id}, include=["metadatas"]
        )
        return len({metadata["source"] for metadata in stored["metadatas"]})
