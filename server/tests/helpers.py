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
