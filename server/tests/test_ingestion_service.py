from datetime import UTC, datetime

import pytest

from app.core.exceptions import DocumentTooLargeError, InvalidDocumentError
from app.infrastructure.captioning.fake import FakeImageCaptioner
from app.infrastructure.documents.readers import FileReader
from app.infrastructure.embeddings.fake import FakeEmbedder
from app.ingestion.chunker import chunk_text
from app.ingestion.ids import chunk_id
from app.services.ingestion_service import IngestionService
from tests.helpers import (
    InMemoryDocumentStore,
    InMemoryRegistry,
    InMemoryVectorStore,
    make_image,
    make_pdf_with_image,
)

FIXED_TIME = datetime(2026, 9, 21, 9, 30, tzinfo=UTC)
# 8 tokens -> 6 words per chunk, 2 words overlap: a 40-word document becomes 10 chunks.
SMALL = {"chunk_max_tokens": 8, "chunk_overlap_tokens": 2}


class OtherModelEmbedder(FakeEmbedder):
    model_name = "another-model"


class FlakyEmbedder(FakeEmbedder):
    """Fails on the first call, works afterwards (a provider error or rate limit)."""

    def __init__(self) -> None:
        super().__init__()
        self.failures_left = 1

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self.failures_left:
            self.failures_left -= 1
            raise RuntimeError("provider unavailable")
        return await super().embed_documents(texts)


class FlakyCaptioner(FakeImageCaptioner):
    """Fails on the first call, works afterwards (a provider error or rate limit)."""

    def __init__(self) -> None:
        super().__init__()
        self.failures_left = 1

    async def caption(self, image: bytes, mime_type: str) -> str:
        if self.failures_left:
            self.failures_left -= 1
            raise RuntimeError("vision provider unavailable")
        return await super().caption(image, mime_type)


class World:
    """One service wired to in-memory fakes, with the parts a test wants to inspect."""

    def __init__(
        self,
        embedder: FakeEmbedder | None = None,
        captioner: FakeImageCaptioner | None = None,
        **overrides,
    ) -> None:
        self.embedder = embedder or FakeEmbedder()
        self.captioner = captioner or FakeImageCaptioner()
        self.vectors = InMemoryVectorStore()
        self.registry = InMemoryRegistry()
        self.documents = InMemoryDocumentStore()
        self.settings = {
            "max_upload_bytes": 1_000_000,
            "min_image_dimension_px": 32,
            "max_images_per_document": 20,
            **SMALL,
            **overrides,
        }
        self.service = self.build(self.embedder, self.captioner)

    def build(
        self, embedder: FakeEmbedder, captioner: FakeImageCaptioner | None = None, **overrides
    ) -> IngestionService:
        merged = {**self.settings, **overrides}
        reader_settings = {
            key: merged.pop(key) for key in ("min_image_dimension_px", "max_images_per_document")
        }
        return IngestionService(
            FileReader(**reader_settings),
            embedder,
            captioner or self.captioner,
            self.vectors,
            self.registry,
            self.documents,
            clock=lambda: FIXED_TIME,
            **merged,
        )


def doc(word_count: int, prefix: str = "w") -> bytes:
    return " ".join(f"{prefix}{i}" for i in range(word_count)).encode()


def pdf_with_image(width: int = 64, height: int = 64, text: str = "") -> bytes:
    return make_pdf_with_image(width, height, text=text)


@pytest.fixture
def world() -> World:
    return World()


@pytest.mark.anyio
async def test_first_upload_is_chunked_embedded_stored_and_recorded(world: World) -> None:
    result = await world.service.ingest("setup.md", doc(40))

    assert result.status == "indexed"
    assert result.document.chunk_count == 10
    assert result.chunks_embedded == 10 == world.embedder.texts_embedded
    assert len(world.vectors.ids_for("setup.md")) == 10
    assert world.documents.files == {"setup.md": doc(40)}
    assert await world.registry.get("setup.md") == result.document
    assert result.document.indexed_at == FIXED_TIME


@pytest.mark.anyio
async def test_an_identical_reupload_makes_zero_embed_calls(world: World) -> None:
    await world.service.ingest("setup.md", doc(40))
    embedded_before = world.embedder.texts_embedded

    result = await world.service.ingest("setup.md", doc(40))

    assert result.status == "unchanged"
    assert result.chunks_embedded == 0
    assert world.embedder.texts_embedded == embedded_before
    assert len(world.vectors.ids_for("setup.md")) == 10  # no duplicates


@pytest.mark.anyio
async def test_the_same_content_under_another_name_is_a_separate_document(world: World) -> None:
    await world.service.ingest("a.md", doc(20))
    result = await world.service.ingest("b.md", doc(20))

    assert result.status == "indexed"
    assert {d.filename for d in await world.service.list_documents()} == {"a.md", "b.md"}
    assert await world.vectors.count_documents() == 2


@pytest.mark.anyio
async def test_a_changed_file_re_embeds_only_new_chunks_and_drops_stale_ones(
    world: World,
) -> None:
    await world.service.ingest("guide.md", doc(40))
    total_before = world.embedder.texts_embedded

    result = await world.service.ingest("guide.md", doc(40) + b" " + doc(20, "extra"))

    longer_text = doc(40).decode() + " " + doc(20, "extra").decode()
    expected_ids = {
        chunk_id(world.embedder.model_name, chunk)
        for chunk in chunk_text(longer_text, "guide.md", max_tokens=8, overlap_tokens=2)
    }
    assert result.status == "indexed"
    assert 0 < result.chunks_embedded < result.document.chunk_count
    assert world.embedder.texts_embedded - total_before == result.chunks_embedded
    assert world.vectors.ids_for("guide.md") == expected_ids  # nothing stale left behind


@pytest.mark.anyio
async def test_shrinking_a_file_removes_the_chunks_that_no_longer_exist(world: World) -> None:
    await world.service.ingest("guide.md", doc(40))

    result = await world.service.ingest("guide.md", doc(10))

    assert len(world.vectors.ids_for("guide.md")) == result.document.chunk_count == 2


@pytest.mark.anyio
async def test_changing_the_embedding_model_re_indexes_even_an_unchanged_file(
    world: World,
) -> None:
    await world.service.ingest("guide.md", doc(40))
    other = OtherModelEmbedder()

    result = await world.build(other).ingest("guide.md", doc(40))

    assert result.status == "indexed"
    assert result.chunks_embedded == result.document.chunk_count == other.texts_embedded
    # Only the new model's chunks remain: the old model's vectors are gone, not mixed in.
    assert len(world.vectors.ids_for("guide.md")) == result.document.chunk_count
    assert all(
        id_ == chunk_id("another-model", record.chunk)
        for id_, record in world.vectors.records.items()
    )


@pytest.mark.anyio
async def test_changing_the_chunk_settings_re_indexes_an_unchanged_file(world: World) -> None:
    await world.service.ingest("guide.md", doc(40))

    result = await world.build(FakeEmbedder(), chunk_max_tokens=16, chunk_overlap_tokens=4).ingest(
        "guide.md", doc(40)
    )

    assert result.status == "indexed"
    assert result.document.chunk_count < 10


@pytest.mark.anyio
async def test_a_folder_in_the_upload_name_is_dropped(world: World) -> None:
    result = await world.service.ingest("../../secrets/notes.md", doc(10))

    assert result.document.filename == "notes.md"
    assert list(world.documents.files) == ["notes.md"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("filename", "content", "error", "message"),
    [
        ("a.md", b"", InvalidDocumentError, "empty"),
        ("a.md", b"   \n\t ", InvalidDocumentError, "No text"),
        ("a.exe", b"MZ", InvalidDocumentError, "Unsupported"),
        ("a.txt", b"\xff\xfe\x00", InvalidDocumentError, "UTF-8"),
        ("..", b"text", InvalidDocumentError, "valid name"),
        ("a.md", b"x" * 101, DocumentTooLargeError, "larger than"),
    ],
)
async def test_bad_uploads_are_rejected_and_leave_no_trace(
    filename: str, content: bytes, error: type[Exception], message: str
) -> None:
    world = World(max_upload_bytes=100)

    with pytest.raises(error, match=message):
        await world.service.ingest(filename, content)

    assert world.embedder.texts_embedded == 0
    assert world.vectors.records == {}
    assert world.registry.documents == {}
    assert world.documents.files == {}


@pytest.mark.anyio
async def test_a_failed_embedding_records_nothing_and_a_retry_succeeds() -> None:
    flaky = FlakyEmbedder()
    world = World(flaky)

    with pytest.raises(RuntimeError):
        await world.service.ingest("guide.md", doc(40))

    assert await world.registry.get("guide.md") is None  # not marked as indexed
    assert world.documents.files == {}

    retry = await world.service.ingest("guide.md", doc(40))

    assert retry.status == "indexed"
    assert len(world.vectors.ids_for("guide.md")) == retry.document.chunk_count


@pytest.mark.anyio
async def test_a_qualifying_image_becomes_its_own_captioned_chunk(world: World) -> None:
    result = await world.service.ingest("diagram.pdf", pdf_with_image(text="see the diagram below"))

    assert result.document.chunk_count == 2  # one text chunk, one caption chunk
    assert world.captioner.images_captioned == 1
    caption_chunks = [r.chunk for r in world.vectors.records.values() if r.chunk.is_image_caption]
    [caption_chunk] = caption_chunks
    assert caption_chunk.page == 1
    assert caption_chunk.source == "diagram.pdf"
    assert "[fake-caption]" in caption_chunk.text


@pytest.mark.anyio
async def test_a_document_with_only_an_image_is_indexed_from_the_caption_alone(
    world: World,
) -> None:
    result = await world.service.ingest("diagram-only.pdf", pdf_with_image())

    assert result.status == "indexed"
    assert result.document.chunk_count == 1
    assert world.embedder.texts_embedded == 1
    [record] = world.vectors.records.values()
    assert record.chunk.is_image_caption


@pytest.mark.anyio
async def test_an_image_smaller_than_the_minimum_produces_no_caption(world: World) -> None:
    result = await world.service.ingest("icon.pdf", pdf_with_image(10, 10, text="a tiny icon"))

    assert result.document.chunk_count == 1  # the text only; the icon is too small to caption
    assert world.captioner.images_captioned == 0


@pytest.mark.anyio
async def test_an_identical_pdf_reupload_makes_zero_caption_calls(world: World) -> None:
    await world.service.ingest("diagram.pdf", pdf_with_image(text="see below"))

    result = await world.service.ingest("diagram.pdf", pdf_with_image(text="see below"))

    assert result.status == "unchanged"
    assert world.captioner.images_captioned == 1  # only the first upload captioned it


@pytest.mark.anyio
async def test_a_standalone_image_upload_is_indexed_from_its_caption_alone(world: World) -> None:
    result = await world.service.ingest("diagram.png", make_image(64, 64))

    assert result.status == "indexed"
    assert result.document.chunk_count == 1
    assert world.captioner.images_captioned == 1
    [record] = world.vectors.records.values()
    assert record.chunk.is_image_caption
    assert record.chunk.page == 1
    assert world.documents.files == {"diagram.png": make_image(64, 64)}


@pytest.mark.anyio
async def test_a_standalone_image_reupload_makes_zero_caption_calls(world: World) -> None:
    await world.service.ingest("diagram.png", make_image(64, 64))

    result = await world.service.ingest("diagram.png", make_image(64, 64))

    assert result.status == "unchanged"
    assert world.captioner.images_captioned == 1


@pytest.mark.anyio
async def test_known_limitation_editing_the_text_recaptions_an_unchanged_image(
    world: World,
) -> None:
    """An edit changes the document's content hash, so the whole file is re-processed, including

    images that did not change. There is no per-image cache keyed on the image bytes, the same
    trade-off already made for embeddings elsewhere in this codebase. A real vision model would be
    called again for an unchanged diagram; the fake one is idempotent by content, so this only shows
    up as a second call count, not as a different caption.
    """
    await world.service.ingest("diagram.pdf", pdf_with_image(text="version one"))

    await world.service.ingest("diagram.pdf", pdf_with_image(text="version two"))

    assert world.captioner.images_captioned == 2


@pytest.mark.anyio
async def test_a_failed_caption_records_nothing_and_a_retry_succeeds() -> None:
    world = World(captioner=FlakyCaptioner())

    with pytest.raises(RuntimeError):
        await world.service.ingest("diagram.pdf", pdf_with_image(text="see below"))

    assert await world.registry.get("diagram.pdf") is None
    assert world.documents.files == {}
    assert world.vectors.records == {}

    retry = await world.service.ingest("diagram.pdf", pdf_with_image(text="see below"))

    assert retry.status == "indexed"


@pytest.mark.anyio
async def test_list_documents_returns_what_was_indexed(world: World) -> None:
    assert await world.service.list_documents() == []

    await world.service.ingest("a.md", doc(10))

    assert [d.filename for d in await world.service.list_documents()] == ["a.md"]
