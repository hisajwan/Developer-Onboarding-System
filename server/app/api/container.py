"""Builds the concrete adapters and services for one app instance, each on first use.

Lives in the API layer because it is where concrete classes are chosen. Creating a Container does no
work, so importing the app touches no files; adapters that open files (Chroma, SQLite) are lazy.

Shared objects are built under a lock: FastAPI runs sync dependencies in a thread pool, and two
threads creating the same new Chroma database at once fails.
"""

import threading
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from langchain_core.runnables import Runnable

from app.agent.langchain_agent import LangChainAgent
from app.agent.tools.registry import ToolRegistry
from app.agent.tools.retrieve_and_answer import RetrieveAndAnswerTool
from app.agent.tools.review_code import ReviewCodeTool
from app.core.config import Settings
from app.domain.ports import (
    ActivityLog,
    Agent,
    ChatHistory,
    ChatSessionRegistry,
    CodeLinter,
    DocumentReader,
    DocumentRegistry,
    DocumentStore,
    Embedder,
    ImageCaptioner,
    LLMClient,
    PasswordHasher,
    ProjectRegistry,
    UserRegistry,
    VectorStore,
)
from app.infrastructure import model_calls
from app.infrastructure.auth.passwords import BcryptPasswordHasher
from app.infrastructure.captioning.registry import create_captioner
from app.infrastructure.chat_models.registry import create_chat_model
from app.infrastructure.documents.readers import FileReader
from app.infrastructure.embeddings.registry import create_embedder
from app.infrastructure.linting.eslint_node import EslintNodeLinter
from app.infrastructure.llm.registry import create_llm_client
from app.infrastructure.storage.disk_documents import DiskDocumentStore
from app.infrastructure.storage.sqlite_activity_log import SqliteActivityLog
from app.infrastructure.storage.sqlite_chat_history import SqliteChatHistory
from app.infrastructure.storage.sqlite_chat_session_registry import SqliteChatSessionRegistry
from app.infrastructure.storage.sqlite_project_registry import SqliteProjectRegistry
from app.infrastructure.storage.sqlite_registry import SqliteDocumentRegistry
from app.infrastructure.storage.sqlite_user_registry import SqliteUserRegistry
from app.infrastructure.vectorstore.chroma_store import ChromaVectorStore, collection_name_for
from app.services.activity_service import ActivityService
from app.services.chat_session_service import ChatSessionService
from app.services.code_review_service import CodeReviewService
from app.services.evaluation_service import EvaluationService
from app.services.ingestion_service import IngestionService
from app.services.project_review_service import ProjectReviewService
from app.services.project_service import ProjectService
from app.services.project_setup_service import ProjectSetupService
from app.services.user_profile_service import UserProfileService

T = TypeVar("T")


def shared(build: Callable[["Container"], T]) -> property:
    """A thread-safe cached property: built at most once per container."""
    key = f"_shared_{build.__name__}"

    @wraps(build)
    def get(self: "Container") -> T:
        try:
            return self.__dict__[key]
        except KeyError:
            pass
        with self._lock:
            if key not in self.__dict__:
                self.__dict__[key] = build(self)
            return self.__dict__[key]

    return property(get)


class Container:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        # Re-entrant: building one object builds the ones it depends on.
        self._lock = threading.RLock()

    @shared
    def embedder(self) -> Embedder:
        return create_embedder(self._settings)

    @shared
    def captioner(self) -> ImageCaptioner:
        return create_captioner(self._settings)

    @shared
    def llm_client(self) -> LLMClient:
        return create_llm_client(self._settings)

    @shared
    def chat_model(self) -> Runnable:
        return create_chat_model(self._settings)

    @shared
    def code_linter(self) -> CodeLinter:
        return EslintNodeLinter.from_settings(self._settings)

    @shared
    def code_review_service(self) -> CodeReviewService:
        return CodeReviewService(self.code_linter, self.llm_client)

    @shared
    def vector_store(self) -> VectorStore:
        return ChromaVectorStore(
            self._settings.chroma_dir, collection_name_for(self.embedder.model_name)
        )

    @shared
    def document_registry(self) -> DocumentRegistry:
        return SqliteDocumentRegistry(self._settings.database_path)

    @shared
    def document_store(self) -> DocumentStore:
        return DiskDocumentStore(self._settings.docs_dir)

    @shared
    def user_registry(self) -> UserRegistry:
        return SqliteUserRegistry(self._settings.database_path)

    @shared
    def project_registry(self) -> ProjectRegistry:
        return SqliteProjectRegistry(self._settings.database_path)

    @shared
    def activity_log(self) -> ActivityLog:
        return SqliteActivityLog(self._settings.database_path)

    @shared
    def activity_service(self) -> ActivityService:
        return ActivityService(self.activity_log, self.document_registry)

    @shared
    def project_review_service(self) -> ProjectReviewService:
        return ProjectReviewService(self.code_review_service, self.activity_log)

    @shared
    def chat_history(self) -> ChatHistory:
        return SqliteChatHistory(self._settings.database_path)

    @shared
    def chat_session_registry(self) -> ChatSessionRegistry:
        return SqliteChatSessionRegistry(self._settings.database_path)

    @shared
    def project_service(self) -> ProjectService:
        return ProjectService(self.user_registry, self.project_registry)

    @shared
    def chat_session_service(self) -> ChatSessionService:
        return ChatSessionService(self.project_service, self.chat_session_registry)

    @shared
    def project_setup_service(self) -> ProjectSetupService:
        return ProjectSetupService(self.project_service, self.chat_session_service)

    @shared
    def user_profile_service(self) -> UserProfileService:
        return UserProfileService(self.user_registry, self.password_hasher)

    @shared
    def password_hasher(self) -> PasswordHasher:
        return BcryptPasswordHasher()

    @shared
    def document_reader(self) -> DocumentReader:
        return FileReader(
            min_image_dimension_px=self._settings.min_image_dimension_px,
            max_images_per_document=self._settings.max_images_per_document,
        )

    @shared
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

    def retrieve_and_answer_tool_for(self, project_id: str) -> RetrieveAndAnswerTool:
        return RetrieveAndAnswerTool(
            self.embedder,
            self.vector_store,
            self.llm_client,
            project_id,
            top_k=self._settings.retrieval_top_k,
        )

    def tool_registry_for(self, project_id: str) -> ToolRegistry:
        return ToolRegistry(
            [
                self.retrieve_and_answer_tool_for(project_id),
                ReviewCodeTool(self.code_review_service),
            ]
        )

    def agent_for(self, project_id: str) -> Agent:
        return LangChainAgent(self.tool_registry_for(project_id), self.chat_model)

    def evaluation_service_for(self, project_id: str) -> EvaluationService:
        return EvaluationService(
            self.agent_for(project_id),
            self.code_review_service,
            call_snapshot=model_calls.snapshot,
        )
