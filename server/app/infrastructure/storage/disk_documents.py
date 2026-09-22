"""Keeps the original uploaded files on disk."""

import asyncio
from pathlib import Path


class DiskDocumentStore:
    def __init__(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        self._directory = directory

    async def save(self, filename: str, content: bytes) -> str:
        """Write the file and return its path. `filename` must already be a bare, safe name."""
        path = self._directory / filename
        await asyncio.to_thread(path.write_bytes, content)
        return str(path)

    async def list_filenames(self) -> list[str]:
        return await asyncio.to_thread(
            lambda: sorted(path.name for path in self._directory.iterdir() if path.is_file())
        )
