"""Keeps the original uploaded files on disk, one subfolder per project."""

import asyncio
from pathlib import Path


class DiskDocumentStore:
    def __init__(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        self._directory = directory

    async def save(self, project_id: str, filename: str, content: bytes) -> str:
        """Write the file and return its path. `filename` must already be a bare, safe name."""
        directory = self._directory / project_id
        await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
        path = directory / filename
        await asyncio.to_thread(path.write_bytes, content)
        return str(path)

    async def list_filenames(self, project_id: str) -> list[str]:
        directory = self._directory / project_id
        return await asyncio.to_thread(_list_filenames, directory)

    async def delete(self, project_id: str, filename: str) -> bool:
        path = self._directory / project_id / filename
        return await asyncio.to_thread(_delete, path)


def _list_filenames(directory: Path) -> list[str]:
    if not directory.is_dir():
        return []
    return sorted(path.name for path in directory.iterdir() if path.is_file())


def _delete(path: Path) -> bool:
    if not path.is_file():
        return False
    path.unlink()
    return True
