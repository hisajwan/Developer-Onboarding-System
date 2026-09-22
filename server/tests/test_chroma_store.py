from pathlib import Path

import pytest

from app.domain.models import Chunk, ChunkRecord
from app.domain.ports import VectorStore
from app.infrastructure.vectorstore.chroma_store import ChromaVectorStore


def record(id_: str, text: str, vector: list[float], source: str = "a.md", index: int = 0,
           caption: bool = False) -> ChunkRecord:
    return ChunkRecord(id_, Chunk(text, source, index, caption), vector)


@pytest.fixture
def store(tmp_path: Path) -> ChromaVectorStore:
    return ChromaVectorStore(tmp_path / "chroma")


def test_satisfies_the_vector_store_port(store: ChromaVectorStore) -> None:
    assert isinstance(store, VectorStore)


@pytest.mark.anyio
async def test_search_returns_the_closest_chunk_first_with_a_similarity_score(
    store: ChromaVectorStore,
) -> None:
    await store.upsert(
        [record("1", "about setup", [1.0, 0.0, 0.0]), record("2", "about billing", [0.0, 1.0, 0.0])]
    )

    results = await store.search([0.9, 0.1, 0.0], top_k=2)

    assert [r.chunk.text for r in results] == ["about setup", "about billing"]
    assert results[0].score > 0.98
    assert results[0].score > results[1].score


@pytest.mark.anyio
async def test_metadata_round_trips(store: ChromaVectorStore) -> None:
    await store.upsert([record("1", "a diagram of the system", [1.0, 0.0], "arch.pdf", 3, True)])

    [result] = await store.search([1.0, 0.0], top_k=1)

    assert result.chunk == Chunk("a diagram of the system", "arch.pdf", 3, is_image_caption=True)


@pytest.mark.anyio
async def test_searching_an_empty_store_or_asking_for_more_than_exists_is_fine(
    store: ChromaVectorStore,
) -> None:
    assert await store.search([1.0, 0.0], top_k=5) == []

    await store.upsert([record("1", "only one", [1.0, 0.0])])

    assert len(await store.search([1.0, 0.0], top_k=5)) == 1


@pytest.mark.anyio
async def test_upserting_the_same_id_again_does_not_duplicate(store: ChromaVectorStore) -> None:
    await store.upsert([record("1", "same", [1.0, 0.0])])
    await store.upsert([record("1", "same", [1.0, 0.0])])

    assert len(await store.search([1.0, 0.0], top_k=10)) == 1


@pytest.mark.anyio
async def test_existing_ids_reports_only_what_is_stored(store: ChromaVectorStore) -> None:
    await store.upsert([record("1", "x", [1.0, 0.0]), record("2", "y", [0.0, 1.0])])

    assert await store.existing_ids(["1", "3", "2"]) == {"1", "2"}
    assert await store.existing_ids([]) == set()


@pytest.mark.anyio
async def test_remove_stale_deletes_only_that_sources_unlisted_chunks(
    store: ChromaVectorStore,
) -> None:
    await store.upsert(
        [
            record("keep", "k", [1.0, 0.0], "a.md", 0),
            record("old", "o", [0.0, 1.0], "a.md", 1),
            record("other", "x", [1.0, 1.0], "b.md", 0),
        ]
    )

    await store.remove_stale("a.md", keep_ids={"keep"})

    assert await store.existing_ids(["keep", "old", "other"]) == {"keep", "other"}


@pytest.mark.anyio
async def test_count_documents_counts_distinct_sources(store: ChromaVectorStore) -> None:
    assert await store.count_documents() == 0

    await store.upsert(
        [
            record("1", "x", [1.0, 0.0], "a.md", 0),
            record("2", "y", [0.0, 1.0], "a.md", 1),
            record("3", "z", [1.0, 1.0], "b.md", 0),
        ]
    )

    assert await store.count_documents() == 2


@pytest.mark.anyio
async def test_chunks_are_still_there_after_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "chroma"
    first = ChromaVectorStore(path)
    await first.upsert([record("1", "survives a restart", [1.0, 0.0], "notes.md")])
    del first

    after_restart = ChromaVectorStore(path)  # a new object over the same folder, like a new process

    [result] = await after_restart.search([1.0, 0.0], top_k=1)
    assert result.chunk.text == "survives a restart"
    assert await after_restart.count_documents() == 1
