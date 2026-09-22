import io

import pytest
from pypdf import PdfWriter

from app.core.exceptions import InvalidDocumentError
from app.domain.ports import DocumentReader
from app.infrastructure.documents.readers import FileReader
from tests.helpers import make_pdf

reader = FileReader()


def test_satisfies_the_reader_port() -> None:
    assert isinstance(reader, DocumentReader)


@pytest.mark.anyio
@pytest.mark.parametrize("name", ["notes.md", "notes.markdown", "notes.txt", "NOTES.MD"])
async def test_text_files_are_decoded(name: str) -> None:
    assert await reader.read_text(name, "# Héllo\nworld".encode()) == "# Héllo\nworld"


@pytest.mark.anyio
async def test_a_byte_order_mark_is_dropped() -> None:
    assert await reader.read_text("a.txt", b"\xef\xbb\xbfhello") == "hello"


@pytest.mark.anyio
async def test_text_that_is_not_utf8_is_rejected() -> None:
    with pytest.raises(InvalidDocumentError, match="UTF-8"):
        await reader.read_text("a.txt", b"\xff\xfe\x00bad")


@pytest.mark.anyio
async def test_unsupported_types_are_rejected_and_the_message_lists_the_supported_ones() -> None:
    with pytest.raises(InvalidDocumentError) as error:
        await reader.read_text("program.exe", b"MZ")

    assert ".exe" in error.value.message
    assert ".pdf" in error.value.message
    assert ".md" in error.value.message


@pytest.mark.anyio
async def test_a_file_without_an_extension_is_rejected() -> None:
    with pytest.raises(InvalidDocumentError, match="Unsupported"):
        await reader.read_text("Makefile", b"all:")


@pytest.mark.anyio
async def test_pdf_text_is_extracted() -> None:
    text = await reader.read_text("guide.pdf", make_pdf("Run npm run dev to start"))

    assert "Run npm run dev to start" in text


@pytest.mark.anyio
async def test_a_pdf_without_text_reads_as_empty() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)

    assert (await reader.read_text("scan.pdf", buffer.getvalue())).strip() == ""


@pytest.mark.anyio
async def test_a_damaged_pdf_is_rejected_cleanly() -> None:
    with pytest.raises(InvalidDocumentError, match="could not be read"):
        await reader.read_text("broken.pdf", b"%PDF-1.4 this is not really a pdf")


@pytest.mark.anyio
async def test_a_password_protected_pdf_is_rejected() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.encrypt("secret")
    buffer = io.BytesIO()
    writer.write(buffer)

    with pytest.raises(InvalidDocumentError, match="Password-protected"):
        await reader.read_text("locked.pdf", buffer.getvalue())
