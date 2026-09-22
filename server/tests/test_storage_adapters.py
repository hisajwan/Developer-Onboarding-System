from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.domain.models import IndexedDocument
from app.domain.ports import DocumentRegistry, DocumentStore
from app.infrastructure.storage.disk_documents import DiskDocumentStore
from app.infrastructure.storage.sqlite_registry import SqliteDocumentRegistry

NOW = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)
PROJECT = "proj-1"
OTHER_PROJECT = "proj-2"


def document(name: str = "a.md", digest: str = "h1", chunks: int = 3, at: datetime = NOW):
    return IndexedDocument(name, digest, "model|500|50", chunks, at)


@pytest.fixture
def registry(tmp_path: Path) -> SqliteDocumentRegistry:
    return SqliteDocumentRegistry(tmp_path / "db" / "app.db")


def test_adapters_satisfy_their_ports(tmp_path: Path, registry: SqliteDocumentRegistry) -> None:
    assert isinstance(registry, DocumentRegistry)
    assert isinstance(DiskDocumentStore(tmp_path / "docs"), DocumentStore)


@pytest.mark.anyio
async def test_registry_round_trips_a_document(registry: SqliteDocumentRegistry) -> None:
    await registry.record(PROJECT, document())

    assert await registry.get(PROJECT, "a.md") == document()


@pytest.mark.anyio
async def test_registry_returns_none_for_an_unknown_file(registry: SqliteDocumentRegistry) -> None:
    assert await registry.get(PROJECT, "missing.md") is None


@pytest.mark.anyio
async def test_the_same_filename_in_two_projects_does_not_collide(
    registry: SqliteDocumentRegistry,
) -> None:
    await registry.record(PROJECT, document(digest="one"))
    await registry.record(OTHER_PROJECT, document(digest="two"))

    assert await registry.get(PROJECT, "a.md") == document(digest="one")
    assert await registry.get(OTHER_PROJECT, "a.md") == document(digest="two")
    assert len(await registry.list_all(PROJECT)) == 1


@pytest.mark.anyio
async def test_recording_the_same_filename_replaces_the_entry(
    registry: SqliteDocumentRegistry,
) -> None:
    await registry.record(PROJECT, document(digest="old", chunks=2))
    await registry.record(PROJECT, document(digest="new", chunks=5))

    assert await registry.get(PROJECT, "a.md") == document(digest="new", chunks=5)
    assert len(await registry.list_all(PROJECT)) == 1


@pytest.mark.anyio
async def test_list_shows_the_newest_first(registry: SqliteDocumentRegistry) -> None:
    await registry.record(PROJECT, document("old.md", at=NOW))
    await registry.record(PROJECT, document("new.md", at=NOW + timedelta(hours=1)))

    assert [d.filename for d in await registry.list_all(PROJECT)] == ["new.md", "old.md"]


@pytest.mark.anyio
async def test_registry_survives_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    await SqliteDocumentRegistry(path).record(PROJECT, document())

    assert await SqliteDocumentRegistry(path).get(PROJECT, "a.md") == document()


@pytest.mark.anyio
async def test_disk_store_writes_the_file_and_lists_names_sorted(tmp_path: Path) -> None:
    store = DiskDocumentStore(tmp_path / "docs")

    where = await store.save(PROJECT, "b.md", b"bee")
    await store.save(PROJECT, "a.md", b"ay")

    assert Path(where).read_bytes() == b"bee"
    assert await store.list_filenames(PROJECT) == ["a.md", "b.md"]


@pytest.mark.anyio
async def test_disk_store_keeps_two_projects_files_separate(tmp_path: Path) -> None:
    store = DiskDocumentStore(tmp_path / "docs")

    await store.save(PROJECT, "a.md", b"mine")
    await store.save(OTHER_PROJECT, "a.md", b"theirs")

    assert await store.list_filenames(PROJECT) == ["a.md"]
    assert await store.list_filenames(OTHER_PROJECT) == ["a.md"]


@pytest.mark.anyio
async def test_disk_store_overwrites_a_file_saved_again(tmp_path: Path) -> None:
    store = DiskDocumentStore(tmp_path / "docs")

    await store.save(PROJECT, "a.md", b"first")
    where = await store.save(PROJECT, "a.md", b"second")

    assert Path(where).read_bytes() == b"second"
    assert await store.list_filenames(PROJECT) == ["a.md"]


@pytest.mark.anyio
async def test_disk_store_lists_nothing_for_a_project_with_no_files(tmp_path: Path) -> None:
    store = DiskDocumentStore(tmp_path / "docs")

    assert await store.list_filenames("never-used") == []
