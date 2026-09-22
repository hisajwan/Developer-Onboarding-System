"""Chroma-backed vector store. Persistent on disk, so chunks survive a backend restart."""

import asyncio
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.domain.models import Chunk, ChunkRecord, RetrievedChunk


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

    async def existing_ids(self, ids: list[str]) -> set[str]:
        if not ids:
            return set()
        found = await asyncio.to_thread(self._collection.get, ids=ids, include=[])
        return set(found["ids"])

    async def upsert(self, records: list[ChunkRecord]) -> None:
        if not records:
            return
        await asyncio.to_thread(
            self._collection.upsert,
            ids=[record.id for record in records],
            embeddings=[record.embedding for record in records],
            documents=[record.chunk.text for record in records],
            metadatas=[
                {
                    "source": record.chunk.source,
                    "index": record.chunk.index,
                    "is_image_caption": record.chunk.is_image_caption,
                }
                for record in records
            ],
        )

    async def remove_stale(self, source: str, keep_ids: set[str]) -> None:
        stored = await asyncio.to_thread(self._collection.get, where={"source": source}, include=[])
        stale = [chunk_id for chunk_id in stored["ids"] if chunk_id not in keep_ids]
        if stale:
            await asyncio.to_thread(self._collection.delete, ids=stale)

    async def search(self, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        result = await asyncio.to_thread(
            self._collection.query,
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        return [
            RetrievedChunk(
                chunk=Chunk(
                    text=text,
                    source=metadata["source"],
                    index=metadata["index"],
                    is_image_caption=metadata["is_image_caption"],
                ),
                score=1.0 - distance,  # cosine distance -> similarity
            )
            for text, metadata, distance in zip(
                result["documents"][0], result["metadatas"][0], result["distances"][0], strict=True
            )
        ]

    async def count_documents(self) -> int:
        stored = await asyncio.to_thread(self._collection.get, include=["metadatas"])
        return len({metadata["source"] for metadata in stored["metadatas"]})
