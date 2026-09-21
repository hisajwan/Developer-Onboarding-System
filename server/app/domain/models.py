"""Framework-free value objects shared across layers (the "atoms" of the backend)."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Chunk:
    text: str
    source: str
    index: int
    is_image_caption: bool = False


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk: Chunk
    score: float


@dataclass(frozen=True, slots=True)
class ToolResult:
    content: str
    sources: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AgentReply:
    content: str
    sources: tuple[str, ...] = ()
    tools_used: tuple[str, ...] = field(default_factory=tuple)
