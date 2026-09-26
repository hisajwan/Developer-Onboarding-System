import pytest

from app.domain.models import Chunk
from app.ingestion.embedding_input import embedding_input, readable_file_name


@pytest.mark.parametrize(
    ("source", "readable"),
    [
        ("Competitor Aegis zero-knowledge.png", "Competitor Aegis zero knowledge"),
        ("dev_setup-guide.md", "dev setup guide"),
        ("README.md", "README"),
    ],
)
def test_file_names_are_made_readable(source: str, readable: str) -> None:
    assert readable_file_name(source) == readable


def test_the_file_name_is_embedded_with_the_text() -> None:
    text = embedding_input(Chunk(text="Run npm install.", source="dev_setup.md", index=0))
    assert text == "File: dev setup\nText:\nRun npm install."


def test_an_image_caption_is_marked_as_one() -> None:
    chunk = Chunk(text="A diagram.", source="Competitor Aegis.png", index=3, is_image_caption=True)
    assert embedding_input(chunk).startswith("File: Competitor Aegis\nImage description:\n")
