from fastapi import APIRouter, UploadFile, status

from app.api.deps import IngestionServiceDep, OwnedProjectDep
from app.schemas.documents import DocumentListResponse, DocumentResponse, UploadResponse

router = APIRouter(prefix="/projects/{project_id}", tags=["documents"])


@router.post("/documents", response_model=UploadResponse)
async def upload_document(
    file: UploadFile, project: OwnedProjectDep, service: IngestionServiceDep
) -> UploadResponse:
    # Read one byte past the limit so an oversized upload is caught without loading all of it.
    content = await file.read(service.max_upload_bytes + 1)
    result = await service.ingest(project.id, file.filename or "", content)
    return UploadResponse.from_domain(result)


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    project: OwnedProjectDep, service: IngestionServiceDep
) -> DocumentListResponse:
    documents = await service.list_documents(project.id)
    return DocumentListResponse(documents=[DocumentResponse.from_domain(d) for d in documents])


@router.delete("/documents/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    filename: str, project: OwnedProjectDep, service: IngestionServiceDep
) -> None:
    await service.delete_document(project.id, filename)
