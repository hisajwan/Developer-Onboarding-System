from fastapi import APIRouter, status

from app.api.deps import OwnedProjectDep, ProjectServiceDep, SessionDep
from app.schemas.projects import (
    CreateProjectRequest,
    ProjectListResponse,
    ProjectResponse,
    RenameProjectRequest,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectListResponse)
async def list_projects(username: SessionDep, service: ProjectServiceDep) -> ProjectListResponse:
    projects = await service.list_projects(username)
    return ProjectListResponse(projects=[ProjectResponse.from_domain(p) for p in projects])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: CreateProjectRequest, username: SessionDep, service: ProjectServiceDep
) -> ProjectResponse:
    project = await service.create_project(username, request.name)
    return ProjectResponse.from_domain(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def rename_project(
    request: RenameProjectRequest,
    project: OwnedProjectDep,
    username: SessionDep,
    service: ProjectServiceDep,
) -> ProjectResponse:
    renamed = await service.rename_project(username, project.id, request.name)
    return ProjectResponse.from_domain(renamed)


@router.post("/{project_id}/select", response_model=ProjectResponse)
async def select_project(
    project: OwnedProjectDep, username: SessionDep, service: ProjectServiceDep
) -> ProjectResponse:
    selected = await service.select_project(username, project.id)
    return ProjectResponse.from_domain(selected)
