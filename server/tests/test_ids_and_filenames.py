import pytest

from app.core.exceptions import InvalidDocumentError
from app.domain.models import Chunk
from app.ingestion.filenames import safe_filename
from app.ingestion.ids import chunk_id, content_hash

BASE = Chunk(text="Install it.", source="setup.md", index=0)
PROJECT = "proj-1"


def test_chunk_id_is_stable() -> None:
    assert chunk_id("model-a", PROJECT, BASE) == chunk_id(
        "model-a", PROJECT, Chunk("Install it.", "setup.md", 0)
    )


@pytest.mark.parametrize(
    "changed",
    [
        Chunk("Install that.", "setup.md", 0),
        Chunk("Install it.", "other.md", 0),
        Chunk("Install it.", "setup.md", 1),
        Chunk("Install it.", "setup.md", 0, is_image_caption=True),
    ],
)
def test_chunk_id_changes_when_any_part_changes(changed: Chunk) -> None:
    assert chunk_id("model-a", PROJECT, changed) != chunk_id("model-a", PROJECT, BASE)


def test_chunk_id_changes_with_the_embedding_model() -> None:
    assert chunk_id("model-a", PROJECT, BASE) != chunk_id("model-b", PROJECT, BASE)


def test_chunk_id_changes_with_the_project() -> None:
    assert chunk_id("model-a", "proj-1", BASE) != chunk_id("model-a", "proj-2", BASE)


def test_neighbouring_parts_cannot_be_confused() -> None:
    assert chunk_id("m", "p", Chunk("bc", "a", 0)) != chunk_id("m", "p", Chunk("c", "ab", 0))


def test_content_hash_depends_on_the_bytes_only() -> None:
    assert content_hash(b"abc") == content_hash(b"abc")
    assert content_hash(b"abc") != content_hash(b"abd")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("readme.md", "readme.md"),
        ("Dev setup guide.md", "Dev setup guide.md"),
        ("../../etc/passwd", "passwd"),
        ("/abs/path/notes.txt", "notes.txt"),
        ("C:\\Users\\me\\doc.pdf", "doc.pdf"),
        ("  padded.md  ", "padded.md"),
    ],
)
def test_safe_filename_keeps_only_the_bare_name(raw: str, expected: str) -> None:
    assert safe_filename(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", ".", "..", "bad\x00name.md", "tab\tname.md"])
def test_safe_filename_rejects_unusable_names(raw: str) -> None:
    with pytest.raises(InvalidDocumentError):
        safe_filename(raw)


def test_safe_filename_rejects_very_long_names() -> None:
    with pytest.raises(InvalidDocumentError, match="longer than"):
        safe_filename("a" * 201 + ".md")
