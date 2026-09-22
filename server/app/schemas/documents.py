from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.domain.models import IndexedDocument, IngestionResult


class DocumentResponse(BaseModel):
    filename: str
    chunk_count: int
    indexed_at: datetime

    @classmethod
    def from_domain(cls, document: IndexedDocument) -> "DocumentResponse":
        return cls(
            filename=document.filename,
            chunk_count=document.chunk_count,
            indexed_at=document.indexed_at,
        )


class UploadResponse(BaseModel):
    document: DocumentResponse
    status: Literal["indexed", "unchanged"]
    chunks_embedded: int

    @classmethod
    def from_domain(cls, result: IngestionResult) -> "UploadResponse":
        return cls(
            document=DocumentResponse.from_domain(result.document),
            status=result.status,
            chunks_embedded=result.chunks_embedded,
        )


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
