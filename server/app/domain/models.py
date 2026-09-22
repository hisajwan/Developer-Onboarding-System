"""Framework-free value objects shared across layers (the "atoms" of the backend)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass(frozen=True, slots=True)
class Chunk:
    text: str
    source: str
    index: int
    is_image_caption: bool = False
    page: int | None = None  # 1-indexed; set for image captions, None for text (not page-tracked)


@dataclass(frozen=True, slots=True)
class ExtractedImage:
    page: int  # 1-indexed
    content: bytes
    mime_type: str


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    text: str
    images: list[ExtractedImage] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ChunkRecord:
    """A chunk ready to store: its deterministic id and its embedding."""

    id: str
    chunk: Chunk
    embedding: list[float]


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk: Chunk
    score: float


@dataclass(frozen=True, slots=True)
class IndexedDocument:
    filename: str
    content_hash: str
    # Embedding model + chunking settings the document was indexed with; a change means re-index.
    index_signature: str
    chunk_count: int
    indexed_at: datetime


IngestionStatus = Literal["indexed", "unchanged"]


@dataclass(frozen=True, slots=True)
class IngestionResult:
    document: IndexedDocument
    status: IngestionStatus
    chunks_embedded: int


@dataclass(frozen=True, slots=True)
class User:
    """A login account, created via `POST /signup` or the seed script (`scripts/create_user.py`)."""

    username: str
    password_hash: str
    first_name: str
    last_name: str
    email: str
    created_at: datetime
    last_project_id: str | None = None  # restored as the active project on the next login


@dataclass(frozen=True, slots=True)
class Project:
    """A workspace of documents and chat history. One owner, no membership or roles."""

    id: str
    owner_username: str
    name: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ChatSession:
    """One conversation thread within a project. A project can have several; its documents and

    retrieval are shared by all of them, only the conversation itself is separate.
    """

    id: str
    project_id: str
    name: str
    created_at: datetime


ChatRole = Literal["user", "assistant"]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """One turn of a session's saved conversation, fed back to the agent as its memory."""

    role: ChatRole
    content: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ToolResult:
    content: str
    sources: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AgentReply:
    content: str
    sources: tuple[str, ...] = ()
    tools_used: tuple[str, ...] = field(default_factory=tuple)
