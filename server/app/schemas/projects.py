from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.models import Project


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class RenameProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ProjectResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, project: Project) -> "ProjectResponse":
        return cls(
            id=project.id,
            name=project.name,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
