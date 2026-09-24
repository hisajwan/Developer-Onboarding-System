"""Deterministic ids, so re-ingesting the same content maps to the same stored chunks."""

import hashlib

from app.domain.models import Chunk
from app.ingestion.embedding_input import EMBEDDING_INPUT_VERSION

_SEPARATOR = "\x1f"  # keeps neighbouring parts from blurring together


def chunk_id(model: str, project_id: str, chunk: Chunk) -> str:
    """Hash of the embedding model and input format, project, source, position, kind and text."""
    parts = [
        model,
        EMBEDDING_INPUT_VERSION,
        project_id,
        chunk.source,
        str(chunk.index),
        str(chunk.is_image_caption),
        chunk.text,
    ]
    return hashlib.sha256(_SEPARATOR.join(parts).encode()).hexdigest()


def content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
