from collections.abc import Callable
from datetime import UTC, datetime

from app.core.exceptions import DocumentTooLargeError, InvalidDocumentError
from app.domain.models import ChunkRecord, IndexedDocument, IngestionResult
from app.domain.ports import DocumentReader, DocumentRegistry, DocumentStore, Embedder, VectorStore
from app.ingestion.chunker import chunk_text
from app.ingestion.filenames import safe_filename
from app.ingestion.ids import chunk_id, content_hash


class IngestionService:
    """Upload -> read -> chunk -> embed -> store, safe to repeat.

    An identical upload (same content, embedding model and chunk settings) is skipped. A changed one
    is re-indexed, embedding only the chunks that are not already stored.
    """

    def __init__(
        self,
        reader: DocumentReader,
        embedder: Embedder,
        vectors: VectorStore,
        registry: DocumentRegistry,
        documents: DocumentStore,
        *,
        max_upload_bytes: int,
        chunk_max_tokens: int,
        chunk_overlap_tokens: int,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._reader = reader
        self._embedder = embedder
        self._vectors = vectors
        self._registry = registry
        self._documents = documents
        self.max_upload_bytes = max_upload_bytes
        self._chunk_max_tokens = chunk_max_tokens
        self._chunk_overlap_tokens = chunk_overlap_tokens
        self._clock = clock

    @property
    def _index_signature(self) -> str:
        return f"{self._embedder.model_name}|{self._chunk_max_tokens}|{self._chunk_overlap_tokens}"

    async def ingest(self, filename: str, content: bytes) -> IngestionResult:
        name = safe_filename(filename)
        if not content:
            raise InvalidDocumentError("The file is empty.")
        if len(content) > self.max_upload_bytes:
            limit_mb = self.max_upload_bytes // (1024 * 1024)
            raise DocumentTooLargeError(f"The file is larger than the {limit_mb} MB limit.")

        digest = content_hash(content)
        previous = await self._registry.get(name)
        if (
            previous is not None
            and previous.content_hash == digest
            and previous.index_signature == self._index_signature
        ):
            return IngestionResult(previous, "unchanged", chunks_embedded=0)

        text = await self._reader.read_text(name, content)
        chunks = chunk_text(
            text,
            name,
            max_tokens=self._chunk_max_tokens,
            overlap_tokens=self._chunk_overlap_tokens,
        )
        if not chunks:
            raise InvalidDocumentError("No text could be extracted from the file.")

        ids = [chunk_id(self._embedder.model_name, chunk) for chunk in chunks]
        already_stored = await self._vectors.existing_ids(ids)
        missing = [
            (id_, chunk)
            for id_, chunk in zip(ids, chunks, strict=True)
            if id_ not in already_stored
        ]

        if missing:
            embeddings = await self._embedder.embed_documents([chunk.text for _, chunk in missing])
            await self._vectors.upsert(
                [
                    ChunkRecord(id_, chunk, embedding)
                    for (id_, chunk), embedding in zip(missing, embeddings, strict=True)
                ]
            )
        await self._vectors.remove_stale(name, keep_ids=set(ids))

        await self._documents.save(name, content)
        document = IndexedDocument(
            filename=name,
            content_hash=digest,
            index_signature=self._index_signature,
            chunk_count=len(chunks),
            indexed_at=self._clock(),
        )
        await self._registry.record(document)
        return IngestionResult(document, "indexed", chunks_embedded=len(missing))

    async def list_documents(self) -> list[IndexedDocument]:
        return await self._registry.list_all()
