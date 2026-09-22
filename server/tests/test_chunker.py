import pytest

from app.ingestion.chunker import chunk_text

# max_tokens=8 -> 6 words per chunk, overlap_tokens=2 -> 2 shared words: chunks start 4 words apart.
SMALL = {"max_tokens": 8, "overlap_tokens": 2}


def words(text: str) -> list[str]:
    return text.split()


def numbered(count: int) -> str:
    return " ".join(f"w{i}" for i in range(count))


def test_short_text_is_a_single_chunk() -> None:
    [chunk] = chunk_text("Run npm install first.", "setup.md")

    assert chunk.text == "Run npm install first."
    assert (chunk.source, chunk.index, chunk.is_image_caption) == ("setup.md", 0, False)


def test_long_text_is_split_into_overlapping_chunks_with_running_indexes() -> None:
    chunks = chunk_text(numbered(20), "doc.md", **SMALL)

    assert [c.index for c in chunks] == [0, 1, 2, 3, 4]
    assert words(chunks[0].text) == ["w0", "w1", "w2", "w3", "w4", "w5"]
    assert words(chunks[1].text)[0] == "w4"
    for previous, following in zip(chunks, chunks[1:], strict=False):
        assert words(previous.text)[-2:] == words(following.text)[:2]


def test_no_word_is_lost_and_no_chunk_exceeds_the_size() -> None:
    text = numbered(101)

    chunks = chunk_text(text, "doc.md", **SMALL)

    assert all(len(words(c.text)) <= 6 for c in chunks)
    assert set(words(text)) == {w for c in chunks for w in words(c.text)}
    assert words(chunks[-1].text)[-1] == "w100"


def test_line_breaks_and_formatting_inside_a_chunk_are_kept() -> None:
    text = "# Title\n\n- one\n- two\n\n```\ncode()\n```"

    [chunk] = chunk_text(text, "doc.md")

    assert chunk.text == text


@pytest.mark.parametrize("text", ["", "   ", "\n\n\t"])
def test_text_without_words_gives_no_chunks(text: str) -> None:
    assert chunk_text(text, "doc.md") == []


def test_chunking_is_deterministic() -> None:
    assert chunk_text(numbered(50), "a.md", **SMALL) == chunk_text(numbered(50), "a.md", **SMALL)


@pytest.mark.parametrize(
    ("max_tokens", "overlap_tokens"), [(0, 0), (8, 8), (8, 9), (8, -1)]
)
def test_invalid_sizes_are_rejected(max_tokens: int, overlap_tokens: int) -> None:
    with pytest.raises(ValueError):
        chunk_text("some text", "doc.md", max_tokens=max_tokens, overlap_tokens=overlap_tokens)


def test_rounding_never_produces_an_endless_loop() -> None:
    # 3 tokens -> 2 words and 2 overlap tokens -> 2 words: the step must still move forward.
    chunks = chunk_text(numbered(10), "doc.md", max_tokens=3, overlap_tokens=2)

    assert len(chunks) >= 2
    assert words(chunks[-1].text)[-1] == "w9"
