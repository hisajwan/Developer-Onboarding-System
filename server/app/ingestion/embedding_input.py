"""The embedding input for a chunk: its file name, then its text. File names can carry meaning the
text never states (e.g. "Competitor X architecture.png"). The stored chunk text is unchanged.
"""

import re
from pathlib import PurePath

from app.domain.models import Chunk

# Bump when the format below changes, so every document is re-embedded on its next upload.
EMBEDDING_INPUT_VERSION = "title-v1"


def readable_file_name(source: str) -> str:
    """'competitor_aegis-zero-knowledge.png' -> 'competitor aegis zero knowledge'."""
    return re.sub(r"[\s_\-]+", " ", PurePath(source).stem).strip()


def embedding_input(chunk: Chunk) -> str:
    kind = "Image description" if chunk.is_image_caption else "Text"
    return f"File: {readable_file_name(chunk.source)}\n{kind}:\n{chunk.text}"
