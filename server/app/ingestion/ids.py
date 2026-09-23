"""Deterministic ids, so re-ingesting the same content maps to the same stored chunks."""

import hashlib

from app.domain.models import Chunk

_SEPARATOR = "\x1f"  # keeps neighbouring parts from blurring together


def chunk_id(model: str, project_id: str, chunk: Chunk) -> str:
    """Hash of the embedding model, project, source, position, kind and text of a chunk."""
    parts = [
        model,
        project_id,
        chunk.source,
        str(chunk.index),
        str(chunk.is_image_caption),
        chunk.text,
    ]
    return hashlib.sha256(_SEPARATOR.join(parts).encode()).hexdigest()


def content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
