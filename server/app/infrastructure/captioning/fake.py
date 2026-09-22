"""Deterministic stand-in for a vision model: describes an image by its hash, size and type.

No network, no key. Different image bytes give different captions; the same bytes always give the
same one.
"""

import hashlib

from app.core.config import Settings


class FakeImageCaptioner:
    def __init__(self) -> None:
        self.images_captioned = 0

    @classmethod
    def from_settings(cls, settings: Settings) -> "FakeImageCaptioner":
        return cls()

    async def caption(self, image: bytes, mime_type: str) -> str:
        self.images_captioned += 1
        digest = hashlib.sha256(image).hexdigest()[:12]
        return f"[fake-caption] a {mime_type} image ({len(image)} bytes, hash {digest})"
