from typing import Protocol, runtime_checkable


@runtime_checkable
class ImageCaptioner(Protocol):
    """Describes an image in words, for a vision-capable model."""

    async def caption(self, image: bytes, mime_type: str) -> str: ...
