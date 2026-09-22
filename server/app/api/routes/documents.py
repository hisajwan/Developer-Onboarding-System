from fastapi import APIRouter, UploadFile

from app.api.deps import IngestionServiceDep
from app.schemas.documents import DocumentListResponse, DocumentResponse, UploadResponse

router = APIRouter(tags=["documents"])


@router.post("/documents", response_model=UploadResponse)
async def upload_document(file: UploadFile, service: IngestionServiceDep) -> UploadResponse:
    # Read one byte past the limit so an oversized upload is caught without loading all of it.
    content = await file.read(service.max_upload_bytes + 1)
    result = await service.ingest(file.filename or "", content)
    return UploadResponse.from_domain(result)


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(service: IngestionServiceDep) -> DocumentListResponse:
    documents = await service.list_documents()
    return DocumentListResponse(documents=[DocumentResponse.from_domain(d) for d in documents])
