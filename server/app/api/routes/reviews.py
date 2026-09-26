from fastapi import APIRouter

from app.api.deps import OwnedProjectDep, ProjectReviewServiceDep
from app.schemas.reviews import ReviewRequest, ReviewResponse

router = APIRouter(prefix="/projects/{project_id}", tags=["reviews"])


@router.post("/reviews", response_model=ReviewResponse)
async def review_code(
    request: ReviewRequest, project: OwnedProjectDep, service: ProjectReviewServiceDep
) -> ReviewResponse:
    review = await service.review(project.id, request.code, request.language)
    return ReviewResponse.from_domain(review)
