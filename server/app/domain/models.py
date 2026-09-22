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
class ToolResult:
    content: str
    sources: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AgentReply:
    content: str
    sources: tuple[str, ...] = ()
    tools_used: tuple[str, ...] = field(default_factory=tuple)
