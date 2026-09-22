"""Plain-class fakes of the storage ports, and a tiny PDF builder, shared by the ingestion tests."""

from app.domain.models import ChunkRecord, IndexedDocument, RetrievedChunk


class InMemoryVectorStore:
    def __init__(self) -> None:
        self.records: dict[str, ChunkRecord] = {}

    def ids_for(self, source: str) -> set[str]:
        return {id_ for id_, record in self.records.items() if record.chunk.source == source}

    async def existing_ids(self, ids: list[str]) -> set[str]:
        return {id_ for id_ in ids if id_ in self.records}

    async def upsert(self, records: list[ChunkRecord]) -> None:
        for record in records:
            self.records[record.id] = record

    async def remove_stale(self, source: str, keep_ids: set[str]) -> None:
        for id_ in self.ids_for(source) - keep_ids:
            del self.records[id_]

    async def search(self, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        scored = [
            RetrievedChunk(
                record.chunk,
                sum(a * b for a, b in zip(query_embedding, record.embedding, strict=True)),
            )
            for record in self.records.values()
        ]
        return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]

    async def count_documents(self) -> int:
        return len({record.chunk.source for record in self.records.values()})


class InMemoryRegistry:
    def __init__(self) -> None:
        self.documents: dict[str, IndexedDocument] = {}

    async def get(self, filename: str) -> IndexedDocument | None:
        return self.documents.get(filename)

    async def record(self, document: IndexedDocument) -> None:
        self.documents[document.filename] = document

    async def list_all(self) -> list[IndexedDocument]:
        return list(self.documents.values())


class InMemoryDocumentStore:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    async def save(self, filename: str, content: bytes) -> str:
        self.files[filename] = content
        return f"memory://{filename}"

    async def list_filenames(self) -> list[str]:
        return sorted(self.files)


def make_pdf_with_image(width: int, height: int, *, mode: str = "L", text: str = "") -> bytes:
    """A one-page PDF with a raw (unfiltered) image XObject of the given size, plus optional text.

    `mode` "L" is grayscale (1 byte/pixel), "RGB" is 3 bytes/pixel. The pixel values don't matter:
    Pillow (via pypdf) re-encodes a raw image to PNG regardless of content.
    """
    channels = {"L": 1, "RGB": 3}[mode]
    pixels = bytes([120]) * (width * height * channels)
    color_space = {"L": "/DeviceGray", "RGB": "/DeviceRGB"}[mode]

    stream = b"q %d 0 0 %d 50 500 cm /Im0 Do Q" % (width, height)
    if text:
        stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET ".encode() + stream
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> /XObject << /Im0 6 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (
            b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace %s "
            b"/BitsPerComponent 8 /Length %d >>\nstream\n"
            % (width, height, color_space.encode(), len(pixels))
        )
        + pixels
        + b"\nendstream",
    ]
    return _assemble_pdf(objects)


def make_pdf(text: str) -> bytes:
    """A minimal one-page PDF whose page shows `text` (no parentheses or backslashes in it)."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    return _assemble_pdf(objects)


def make_two_page_pdf_with_image(width: int, height: int, *, image_pages: set[int]) -> bytes:
    """A two-page PDF, empty except for a raw grayscale image XObject on each page in `image_pages`

    (a subset of {1, 2}). Both pages that get one reuse the same image object, so a PDF with images
    on both pages still has exactly one distinct XObject, matching how a PDF viewer would reuse it.
    """
    pixels = bytes([120]) * (width * height)
    image_stream = b"q %d 0 0 %d 50 500 cm /Im0 Do Q" % (width, height)
    resources = b"/Resources << /XObject << /Im0 7 0 R >> >> >>"
    no_resources = b"/Resources << >> >>"
    page_streams = [image_stream if page in image_pages else b"" for page in (1, 2)]
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 5 0 R "
        + (resources if 1 in image_pages else no_resources),
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 6 0 R "
        + (resources if 2 in image_pages else no_resources),
        b"<< /Length " + str(len(page_streams[0])).encode() + b" >>\nstream\n"
        + page_streams[0] + b"\nendstream",
        b"<< /Length " + str(len(page_streams[1])).encode() + b" >>\nstream\n"
        + page_streams[1] + b"\nendstream",
        (b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceGray "
         b"/BitsPerComponent 8 /Length %d >>\nstream\n" % (width, height, len(pixels)))
        + pixels + b"\nendstream",
    ]
    return _assemble_pdf(objects)


def _assemble_pdf(objects: list[bytes]) -> bytes:
    out = b"%PDF-1.4\n"
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode() + b"0000000000 65535 f \n"
    out += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n"
    ).encode()
    return out
