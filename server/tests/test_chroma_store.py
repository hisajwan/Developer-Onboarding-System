from pathlib import Path

import pytest

from app.domain.models import Chunk, ChunkRecord
from app.domain.ports import VectorStore
from app.infrastructure.vectorstore.chroma_store import ChromaVectorStore, collection_name_for

PROJECT = "proj-1"
OTHER_PROJECT = "proj-2"


def record(id_: str, text: str, vector: list[float], source: str = "a.md", index: int = 0,
           caption: bool = False, page: int | None = None) -> ChunkRecord:
    return ChunkRecord(id_, Chunk(text, source, index, caption, page), vector)


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
        PROJECT,
        [
            record("1", "about setup", [1.0, 0.0, 0.0]),
            record("2", "about billing", [0.0, 1.0, 0.0]),
        ],
    )

    results = await store.search(PROJECT, [0.9, 0.1, 0.0], top_k=2)

    assert [r.chunk.text for r in results] == ["about setup", "about billing"]
    assert results[0].score > 0.98
    assert results[0].score > results[1].score


@pytest.mark.anyio
async def test_metadata_round_trips(store: ChromaVectorStore) -> None:
    text = "a diagram of the system"
    await store.upsert(PROJECT, [record("1", text, [1.0, 0.0], "arch.pdf", 3, True, page=2)])

    [result] = await store.search(PROJECT, [1.0, 0.0], top_k=1)

    assert result.chunk == Chunk(text, "arch.pdf", 3, is_image_caption=True, page=2)


@pytest.mark.anyio
async def test_a_chunk_with_no_page_round_trips_as_none(store: ChromaVectorStore) -> None:
    await store.upsert(PROJECT, [record("1", "plain text", [1.0, 0.0])])

    [result] = await store.search(PROJECT, [1.0, 0.0], top_k=1)

    assert result.chunk.page is None


@pytest.mark.anyio
async def test_searching_an_empty_store_or_asking_for_more_than_exists_is_fine(
    store: ChromaVectorStore,
) -> None:
    assert await store.search(PROJECT, [1.0, 0.0], top_k=5) == []

    await store.upsert(PROJECT, [record("1", "only one", [1.0, 0.0])])

    assert len(await store.search(PROJECT, [1.0, 0.0], top_k=5)) == 1


@pytest.mark.anyio
async def test_upserting_the_same_id_again_does_not_duplicate(store: ChromaVectorStore) -> None:
    await store.upsert(PROJECT, [record("1", "same", [1.0, 0.0])])
    await store.upsert(PROJECT, [record("1", "same", [1.0, 0.0])])

    assert len(await store.search(PROJECT, [1.0, 0.0], top_k=10)) == 1


@pytest.mark.anyio
async def test_existing_ids_reports_only_what_is_stored(store: ChromaVectorStore) -> None:
    await store.upsert(PROJECT, [record("1", "x", [1.0, 0.0]), record("2", "y", [0.0, 1.0])])

    assert await store.existing_ids(PROJECT, ["1", "3", "2"]) == {"1", "2"}
    assert await store.existing_ids(PROJECT, []) == set()


@pytest.mark.anyio
async def test_remove_stale_deletes_only_that_sources_unlisted_chunks(
    store: ChromaVectorStore,
) -> None:
    await store.upsert(
        PROJECT,
        [
            record("keep", "k", [1.0, 0.0], "a.md", 0),
            record("old", "o", [0.0, 1.0], "a.md", 1),
            record("other", "x", [1.0, 1.0], "b.md", 0),
        ],
    )

    await store.remove_stale(PROJECT, "a.md", keep_ids={"keep"})

    assert await store.existing_ids(PROJECT, ["keep", "old", "other"]) == {"keep", "other"}


@pytest.mark.anyio
async def test_count_documents_counts_distinct_sources(store: ChromaVectorStore) -> None:
    assert await store.count_documents(PROJECT) == 0

    await store.upsert(
        PROJECT,
        [
            record("1", "x", [1.0, 0.0], "a.md", 0),
            record("2", "y", [0.0, 1.0], "a.md", 1),
            record("3", "z", [1.0, 1.0], "b.md", 0),
        ],
    )

    assert await store.count_documents(PROJECT) == 2


@pytest.mark.anyio
async def test_chunks_are_still_there_after_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "chroma"
    first = ChromaVectorStore(path)
    await first.upsert(PROJECT, [record("1", "survives a restart", [1.0, 0.0], "notes.md")])
    del first

    after_restart = ChromaVectorStore(path)  # a new object over the same folder, like a new process

    [result] = await after_restart.search(PROJECT, [1.0, 0.0], top_k=1)
    assert result.chunk.text == "survives a restart"
    assert await after_restart.count_documents(PROJECT) == 1


@pytest.mark.anyio
async def test_search_is_scoped_to_its_project(store: ChromaVectorStore) -> None:
    # Distinct ids, as real chunk ids always are (chunk_id() bakes the project id into the hash) -
    # the point here is that the `where` filter, not distinct ids, is what keeps them apart.
    await store.upsert(PROJECT, [record("p1-1", "mine", [1.0, 0.0], "a.md")])
    await store.upsert(OTHER_PROJECT, [record("p2-1", "theirs", [1.0, 0.0], "a.md")])

    mine = await store.search(PROJECT, [1.0, 0.0], top_k=5)
    theirs = await store.search(OTHER_PROJECT, [1.0, 0.0], top_k=5)

    assert [r.chunk.text for r in mine] == ["mine"]
    assert [r.chunk.text for r in theirs] == ["theirs"]


@pytest.mark.anyio
async def test_removing_stale_chunks_in_one_project_leaves_the_other_alone(
    store: ChromaVectorStore,
) -> None:
    await store.upsert(PROJECT, [record("p1-1", "mine", [1.0, 0.0], "a.md")])
    await store.upsert(OTHER_PROJECT, [record("p2-1", "theirs", [1.0, 0.0], "a.md")])

    await store.remove_stale(PROJECT, "a.md", keep_ids=set())

    assert await store.existing_ids(PROJECT, ["p1-1"]) == set()
    assert await store.existing_ids(OTHER_PROJECT, ["p2-1"]) == {"p2-1"}


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("fake-hash-256", "documents-fake-hash-256"),
        ("gemini-embedding-001", "documents-gemini-embedding-001"),
        ("models/text embedding:v2", "documents-models-text-embedding-v2"),
    ],
)
def test_each_embedding_model_gets_its_own_valid_collection_name(model: str, expected: str) -> None:
    assert collection_name_for(model) == expected


@pytest.mark.anyio
async def test_vectors_of_a_different_size_go_to_their_own_collection(tmp_path: Path) -> None:
    path = tmp_path / "chroma"
    small = ChromaVectorStore(path, collection_name_for("small-model"))
    large = ChromaVectorStore(path, collection_name_for("large-model"))

    await small.upsert("p", [ChunkRecord("a", Chunk(text="x", source="s.md", index=0), [1.0, 0.0])])
    await large.upsert("p", [ChunkRecord("b", Chunk(text="y", source="s.md", index=0), [0.0] * 8)])

    assert await small.existing_ids("p", ["a", "b"]) == {"a"}
    assert await large.existing_ids("p", ["a", "b"]) == {"b"}
