"""Reads uploaded files into text and any embedded images. A new file type = one function + one

line in `_READERS`.
"""

import asyncio
from collections.abc import Callable
from io import BytesIO
from pathlib import PurePosixPath

from PIL import Image
from pypdf import PdfReader

from app.core.exceptions import InvalidDocumentError
from app.domain.models import ExtractedImage, ParsedDocument

# Pillow's detected format, mapped to a mime type a vision model expects. Anything else is skipped.
_PIL_FORMAT_TO_MIME = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}


def _qualifying_mime_type(image: Image.Image, min_image_dimension_px: int) -> str | None:
    """The mime type to use for this image, or None if it's too small or an unsupported format."""
    mime_type = _PIL_FORMAT_TO_MIME.get(image.format or "")
    if mime_type is None:
        return None
    width, height = image.size
    return mime_type if min(width, height) >= min_image_dimension_px else None


def _read_text(
    content: bytes, min_image_dimension_px: int, max_images_per_document: int
) -> ParsedDocument:
    try:
        return ParsedDocument(text=content.decode("utf-8-sig"))
    except UnicodeDecodeError:
        raise InvalidDocumentError("The file is not valid UTF-8 text.") from None


def _extract_images(
    reader: PdfReader, min_image_dimension_px: int, max_images_per_document: int
) -> list[ExtractedImage]:
    images: list[ExtractedImage] = []
    for page_number, page in enumerate(reader.pages, start=1):
        for image in page.images:
            if len(images) >= max_images_per_document:
                return images
            try:
                mime_type = _qualifying_mime_type(image.image, min_image_dimension_px)
            except Exception:  # noqa: BLE001 - one unreadable embedded image should not fail the upload
                continue
            if mime_type is None:
                continue
            images.append(ExtractedImage(page=page_number, content=image.data, mime_type=mime_type))
    return images


def _read_pdf(
    content: bytes, min_image_dimension_px: int, max_images_per_document: int
) -> ParsedDocument:
    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            raise InvalidDocumentError("Password-protected PDFs are not supported.")
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
        images = _extract_images(reader, min_image_dimension_px, max_images_per_document)
    except InvalidDocumentError:
        raise
    except Exception as exc:  # pypdf raises many error types for damaged files
        raise InvalidDocumentError("The PDF could not be read.") from exc
    return ParsedDocument(text=text, images=images)


def _read_image(
    content: bytes, min_image_dimension_px: int, max_images_per_document: int
) -> ParsedDocument:
    """A standalone image upload: no text, just the one image, captioned like any PDF figure."""
    try:
        image = Image.open(BytesIO(content))
        image.load()  # Image.open only reads the header; force a full decode now, not later.
    except Exception as exc:
        raise InvalidDocumentError("The image could not be read.") from exc

    mime_type = _qualifying_mime_type(image, min_image_dimension_px)
    if mime_type is None:
        raise InvalidDocumentError(
            f"The image must be PNG, JPEG or WEBP and at least {min_image_dimension_px}px "
            "on its shortest side."
        )
    image_record = ExtractedImage(page=1, content=content, mime_type=mime_type)
    return ParsedDocument(text="", images=[image_record])


_READERS: dict[str, Callable[[bytes, int, int], ParsedDocument]] = {
    ".md": _read_text,
    ".markdown": _read_text,
    ".txt": _read_text,
    ".pdf": _read_pdf,
    ".png": _read_image,
    ".jpg": _read_image,
    ".jpeg": _read_image,
    ".webp": _read_image,
}


class FileReader:
    def __init__(self, *, min_image_dimension_px: int, max_images_per_document: int) -> None:
        self._min_image_dimension_px = min_image_dimension_px
        self._max_images_per_document = max_images_per_document

    async def read(self, filename: str, content: bytes) -> ParsedDocument:
        suffix = PurePosixPath(filename).suffix.lower()
        reader = _READERS.get(suffix)
        if reader is None:
            supported = ", ".join(sorted(_READERS))
            raise InvalidDocumentError(
                f"Unsupported file type '{suffix}'. Use one of: {supported}."
            )
        return await asyncio.to_thread(
            reader, content, self._min_image_dimension_px, self._max_images_per_document
        )
