from typing import Protocol, runtime_checkable


@runtime_checkable
class DocumentReader(Protocol):
    """Turns an uploaded file into plain text. Raises InvalidDocumentError for unreadable files."""

    async def read_text(self, filename: str, content: bytes) -> str: ...
