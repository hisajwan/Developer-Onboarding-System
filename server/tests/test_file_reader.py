import pytest
from pypdf import PdfWriter

from app.core.exceptions import InvalidDocumentError
from app.domain.ports import DocumentReader
from app.infrastructure.documents.readers import FileReader
from tests.helpers import make_pdf, make_pdf_with_image, make_two_page_pdf_with_image

reader = FileReader(min_image_dimension_px=32, max_images_per_document=20)


def test_satisfies_the_reader_port() -> None:
    assert isinstance(reader, DocumentReader)


@pytest.mark.anyio
@pytest.mark.parametrize("name", ["notes.md", "notes.markdown", "notes.txt", "NOTES.MD"])
async def test_text_files_are_decoded(name: str) -> None:
    parsed = await reader.read(name, "# Héllo\nworld".encode())

    assert parsed.text == "# Héllo\nworld"
    assert parsed.images == []


@pytest.mark.anyio
async def test_a_byte_order_mark_is_dropped() -> None:
    assert (await reader.read("a.txt", b"\xef\xbb\xbfhello")).text == "hello"


@pytest.mark.anyio
async def test_text_that_is_not_utf8_is_rejected() -> None:
    with pytest.raises(InvalidDocumentError, match="UTF-8"):
        await reader.read("a.txt", b"\xff\xfe\x00bad")


@pytest.mark.anyio
async def test_unsupported_types_are_rejected_and_the_message_lists_the_supported_ones() -> None:
    with pytest.raises(InvalidDocumentError) as error:
        await reader.read("program.exe", b"MZ")

    assert ".exe" in error.value.message
    assert ".pdf" in error.value.message
    assert ".md" in error.value.message


@pytest.mark.anyio
async def test_a_file_without_an_extension_is_rejected() -> None:
    with pytest.raises(InvalidDocumentError, match="Unsupported"):
        await reader.read("Makefile", b"all:")


@pytest.mark.anyio
async def test_pdf_text_is_extracted() -> None:
    parsed = await reader.read("guide.pdf", make_pdf("Run npm run dev to start"))

    assert "Run npm run dev to start" in parsed.text
    assert parsed.images == []


@pytest.mark.anyio
async def test_a_pdf_without_text_reads_as_empty() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    import io

    buffer = io.BytesIO()
    writer.write(buffer)

    assert (await reader.read("scan.pdf", buffer.getvalue())).text.strip() == ""


@pytest.mark.anyio
async def test_a_damaged_pdf_is_rejected_cleanly() -> None:
    with pytest.raises(InvalidDocumentError, match="could not be read"):
        await reader.read("broken.pdf", b"%PDF-1.4 this is not really a pdf")


@pytest.mark.anyio
async def test_a_password_protected_pdf_is_rejected() -> None:
    import io

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.encrypt("secret")
    buffer = io.BytesIO()
    writer.write(buffer)

    with pytest.raises(InvalidDocumentError, match="Password-protected"):
        await reader.read("locked.pdf", buffer.getvalue())


@pytest.mark.anyio
async def test_an_embedded_image_is_extracted_with_its_page_and_mime_type() -> None:
    parsed = await reader.read("diagram.pdf", make_pdf_with_image(64, 64, text="see below"))

    assert "see below" in parsed.text
    [image] = parsed.images
    assert (image.page, image.mime_type) == (1, "image/png")
    assert len(image.content) > 0


@pytest.mark.anyio
async def test_an_image_reports_the_page_it_is_actually_on() -> None:
    pdf = make_two_page_pdf_with_image(60, 60, image_pages={2})

    [image] = (await reader.read("two-pages.pdf", pdf)).images

    assert image.page == 2


@pytest.mark.anyio
async def test_images_smaller_than_the_minimum_are_skipped() -> None:
    tiny = FileReader(min_image_dimension_px=32, max_images_per_document=20)

    parsed = await tiny.read("icon.pdf", make_pdf_with_image(10, 10))

    assert parsed.images == []


@pytest.mark.anyio
async def test_the_minimum_dimension_is_configurable() -> None:
    permissive = FileReader(min_image_dimension_px=5, max_images_per_document=20)

    parsed = await permissive.read("icon.pdf", make_pdf_with_image(10, 10))

    assert len(parsed.images) == 1


@pytest.mark.anyio
async def test_a_document_with_only_a_qualifying_image_has_no_text_but_still_has_images() -> None:
    parsed = await reader.read("diagram-only.pdf", make_pdf_with_image(64, 64))

    assert parsed.text.strip() == ""
    assert len(parsed.images) == 1


@pytest.mark.anyio
async def test_the_image_cap_per_document_is_respected() -> None:
    capped = FileReader(min_image_dimension_px=32, max_images_per_document=1)
    two_images = make_two_page_pdf_with_image(60, 60, image_pages={1, 2})

    assert len((await reader.read("two.pdf", two_images)).images) == 2  # uncapped: both found
    assert len((await capped.read("two.pdf", two_images)).images) == 1  # capped: stops at the limit
