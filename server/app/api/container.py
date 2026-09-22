"""Builds the concrete adapters and services for one app instance, each on first use.

Lives in the API layer because it is where concrete classes are chosen. Creating a Container does no
work, so importing the app touches no files; adapters that open files (Chroma, SQLite) are lazy.
"""

from functools import cached_property

from app.core.config import Settings
from app.domain.ports import (
    DocumentReader,
    DocumentRegistry,
    DocumentStore,
    Embedder,
    ImageCaptioner,
    VectorStore,
)
from app.infrastructure.captioning.registry import create_captioner
from app.infrastructure.documents.readers import FileReader
from app.infrastructure.embeddings.registry import create_embedder
from app.infrastructure.storage.disk_documents import DiskDocumentStore
from app.infrastructure.storage.sqlite_registry import SqliteDocumentRegistry
from app.infrastructure.vectorstore.chroma_store import ChromaVectorStore
from app.services.ingestion_service import IngestionService


class Container:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @cached_property
    def embedder(self) -> Embedder:
        return create_embedder(self._settings)

    @cached_property
    def captioner(self) -> ImageCaptioner:
        return create_captioner(self._settings)

    @cached_property
    def vector_store(self) -> VectorStore:
        return ChromaVectorStore(self._settings.chroma_dir)

    @cached_property
    def document_registry(self) -> DocumentRegistry:
        return SqliteDocumentRegistry(self._settings.database_path)

    @cached_property
    def document_store(self) -> DocumentStore:
        return DiskDocumentStore(self._settings.docs_dir)

    @cached_property
    def document_reader(self) -> DocumentReader:
        return FileReader(
            min_image_dimension_px=self._settings.min_image_dimension_px,
            max_images_per_document=self._settings.max_images_per_document,
        )

    @cached_property
    def ingestion_service(self) -> IngestionService:
        return IngestionService(
            self.document_reader,
            self.embedder,
            self.captioner,
            self.vector_store,
            self.document_registry,
            self.document_store,
            max_upload_bytes=self._settings.max_upload_bytes,
            chunk_max_tokens=self._settings.chunk_max_tokens,
            chunk_overlap_tokens=self._settings.chunk_overlap_tokens,
        )
