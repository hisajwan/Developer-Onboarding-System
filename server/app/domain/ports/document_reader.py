from typing import Protocol, runtime_checkable

from app.domain.models import ParsedDocument


@runtime_checkable
class DocumentReader(Protocol):
    """Turns an uploaded file into text and any embedded images. Raises InvalidDocumentError

    for unreadable files.
    """

    async def read(self, filename: str, content: bytes) -> ParsedDocument: ...
