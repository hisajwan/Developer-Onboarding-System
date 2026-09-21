"""Deterministic stand-in for an embedding model: hashes words into a fixed-size unit vector.

Texts that share words get similar vectors, so similarity search works with no network or key.
"""

import hashlib
import math
import re

from app.core.config import Settings

_WORD = re.compile(r"[a-z0-9]+")


class FakeEmbedder:
    model_name = "fake-hash-256"
    dimensions = 256

    def __init__(self) -> None:
        self.texts_embedded = 0

    @classmethod
    def from_settings(cls, settings: Settings) -> "FakeEmbedder":
        return cls()

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.texts_embedded += len(texts)
        return [self._vector(text) for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        self.texts_embedded += 1
        return self._vector(text)

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for word in _WORD.findall(text.lower()):
            digest = hashlib.sha256(word.encode()).digest()
            vector[int.from_bytes(digest[:4], "big") % self.dimensions] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector
