"""Splits text into overlapping chunks of roughly N tokens, without needing a tokenizer.

A token is approximated as 0.75 of a word, the usual rule of thumb for English. Chunks are cut
from the original text, so line breaks and formatting inside a chunk are kept.
"""

import re

from app.domain.models import Chunk

_WORDS_PER_TOKEN = 0.75
_WORD = re.compile(r"\S+")


def chunk_text(
    text: str,
    source: str,
    *,
    max_tokens: int = 500,
    overlap_tokens: int = 50,
) -> list[Chunk]:
    if max_tokens < 1 or not 0 <= overlap_tokens < max_tokens:
        raise ValueError("Chunk size must be positive and the overlap smaller than the size.")

    size = max(1, round(max_tokens * _WORDS_PER_TOKEN))
    step = max(1, size - round(overlap_tokens * _WORDS_PER_TOKEN))
    words = list(_WORD.finditer(text))

    chunks: list[Chunk] = []
    start = 0
    while start < len(words):
        window = words[start : start + size]
        chunks.append(
            Chunk(text=text[window[0].start() : window[-1].end()], source=source, index=len(chunks))
        )
        if start + size >= len(words):
            break
        start += step
    return chunks
