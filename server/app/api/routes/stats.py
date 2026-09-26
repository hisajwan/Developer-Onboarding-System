from fastapi import APIRouter

from app.api.deps import ActivityServiceDep, OwnedProjectDep
from app.schemas.stats import StatsResponse

router = APIRouter(prefix="/projects/{project_id}", tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
async def project_stats(project: OwnedProjectDep, service: ActivityServiceDep) -> StatsResponse:
    return StatsResponse.from_domain(await service.stats(project.id))
