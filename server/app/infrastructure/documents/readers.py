"""Reads uploaded files into plain text. A new file type = one function + one line in `_READERS`."""

import asyncio
from collections.abc import Callable
from io import BytesIO
from pathlib import PurePosixPath

from pypdf import PdfReader

from app.core.exceptions import InvalidDocumentError


def _read_text(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InvalidDocumentError("The file is not valid UTF-8 text.") from None


def _read_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            raise InvalidDocumentError("Password-protected PDFs are not supported.")
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except InvalidDocumentError:
        raise
    except Exception as exc:  # pypdf raises many error types for damaged files
        raise InvalidDocumentError("The PDF could not be read.") from exc


_READERS: dict[str, Callable[[bytes], str]] = {
    ".md": _read_text,
    ".markdown": _read_text,
    ".txt": _read_text,
    ".pdf": _read_pdf,
}


class FileReader:
    async def read_text(self, filename: str, content: bytes) -> str:
        suffix = PurePosixPath(filename).suffix.lower()
        reader = _READERS.get(suffix)
        if reader is None:
            supported = ", ".join(sorted(_READERS))
            raise InvalidDocumentError(
                f"Unsupported file type '{suffix}'. Use one of: {supported}."
            )
        return await asyncio.to_thread(reader, content)
