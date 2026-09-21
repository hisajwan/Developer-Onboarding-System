import math

import pytest

from app.core.config import Settings
from app.domain.ports import Embedder
from app.infrastructure.embeddings.fake import FakeEmbedder


@pytest.fixture
def embedder() -> FakeEmbedder:
    return FakeEmbedder.from_settings(Settings(_env_file=None))


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def test_satisfies_the_embedder_port(embedder: FakeEmbedder) -> None:
    assert isinstance(embedder, Embedder)


@pytest.mark.anyio
async def test_vectors_are_deterministic_and_unit_length(embedder: FakeEmbedder) -> None:
    first = await embedder.embed_query("Set up the dev environment")
    second = await embedder.embed_query("Set up the dev environment")

    assert first == second
    assert len(first) == embedder.dimensions
    assert math.isclose(math.sqrt(sum(v * v for v in first)), 1.0)


@pytest.mark.anyio
async def test_query_and_document_embeddings_match(embedder: FakeEmbedder) -> None:
    [document] = await embedder.embed_documents(["deploy to staging"])

    assert document == await embedder.embed_query("deploy to staging")


@pytest.mark.anyio
async def test_texts_sharing_words_are_closer_than_unrelated_texts(embedder: FakeEmbedder) -> None:
    query = await embedder.embed_query("how do I set up the dev environment")
    related = await embedder.embed_query("dev environment setup guide")
    unrelated = await embedder.embed_query("quarterly invoice payment terms")

    assert cosine(query, related) > cosine(query, unrelated)


@pytest.mark.anyio
async def test_text_without_words_gives_a_zero_vector_not_an_error(embedder: FakeEmbedder) -> None:
    assert await embedder.embed_query("...") == [0.0] * embedder.dimensions


@pytest.mark.anyio
async def test_it_counts_how_many_texts_it_embedded(embedder: FakeEmbedder) -> None:
    await embedder.embed_documents(["a", "b", "c"])
    await embedder.embed_query("d")

    assert embedder.texts_embedded == 4
