from typing import Protocol, runtime_checkable


@runtime_checkable
class DocumentStore(Protocol):
    """Keeps the original uploaded files so they can be re-indexed later."""

    async def save(self, project_id: str, filename: str, content: bytes) -> str: ...

    async def list_filenames(self, project_id: str) -> list[str]: ...

    async def delete(self, project_id: str, filename: str) -> bool:
        """True if a file was removed, False if there was none to remove."""
        ...
