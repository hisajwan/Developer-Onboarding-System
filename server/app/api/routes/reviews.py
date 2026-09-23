from fastapi import APIRouter

from app.api.deps import CodeReviewServiceDep, OwnedProjectDep
from app.schemas.reviews import ReviewRequest, ReviewResponse

router = APIRouter(prefix="/projects/{project_id}", tags=["reviews"])


@router.post("/reviews", response_model=ReviewResponse)
async def review_code(
    request: ReviewRequest, project: OwnedProjectDep, service: CodeReviewServiceDep
) -> ReviewResponse:
    # `project` is only the ownership check: a review reads no project data.
    review = await service.review(request.code, request.language)
    return ReviewResponse.from_domain(review)
