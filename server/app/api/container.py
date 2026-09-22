"""Builds the concrete adapters and services for one app instance, each on first use.

Lives in the API layer because it is where concrete classes are chosen. Creating a Container does no
work, so importing the app touches no files; adapters that open files (Chroma, SQLite) are lazy.
"""

from functools import cached_property

from langchain_core.language_models.chat_models import BaseChatModel

from app.agent.langchain_agent import LangChainAgent
from app.agent.tools.registry import ToolRegistry
from app.agent.tools.retrieve_and_answer import RetrieveAndAnswerTool
from app.core.config import Settings
from app.domain.ports import (
    Agent,
    DocumentReader,
    DocumentRegistry,
    DocumentStore,
    Embedder,
    ImageCaptioner,
    LLMClient,
    UserRegistry,
    VectorStore,
)
from app.infrastructure.captioning.registry import create_captioner
from app.infrastructure.chat_models.registry import create_chat_model
from app.infrastructure.documents.readers import FileReader
from app.infrastructure.embeddings.registry import create_embedder
from app.infrastructure.llm.registry import create_llm_client
from app.infrastructure.storage.disk_documents import DiskDocumentStore
from app.infrastructure.storage.sqlite_registry import SqliteDocumentRegistry
from app.infrastructure.storage.sqlite_user_registry import SqliteUserRegistry
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
    def llm_client(self) -> LLMClient:
        return create_llm_client(self._settings)

    @cached_property
    def chat_model(self) -> BaseChatModel:
        return create_chat_model(self._settings)

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
    def user_registry(self) -> UserRegistry:
        return SqliteUserRegistry(self._settings.database_path)

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

    @cached_property
    def retrieve_and_answer_tool(self) -> RetrieveAndAnswerTool:
        return RetrieveAndAnswerTool(
            self.embedder, self.vector_store, self.llm_client, top_k=self._settings.retrieval_top_k
        )

    @cached_property
    def tool_registry(self) -> ToolRegistry:
        return ToolRegistry([self.retrieve_and_answer_tool])

    @cached_property
    def agent(self) -> Agent:
        return LangChainAgent(self.tool_registry, self.chat_model)
