from fastapi import APIRouter, status

from app.api.deps import SessionDep, UserProfileServiceDep
from app.schemas.profile import ChangePasswordRequest, ProfileResponse, UpdateProfileRequest

router = APIRouter(prefix="/me", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile(username: SessionDep, service: UserProfileServiceDep) -> ProfileResponse:
    user = await service.get_profile(username)
    return ProfileResponse.from_domain(user)


@router.patch("", response_model=ProfileResponse)
async def update_profile(
    request: UpdateProfileRequest, username: SessionDep, service: UserProfileServiceDep
) -> ProfileResponse:
    user = await service.update_profile(username, request.first_name, request.last_name)
    return ProfileResponse.from_domain(user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: ChangePasswordRequest, username: SessionDep, service: UserProfileServiceDep
) -> None:
    await service.change_password(username, request.current_password, request.new_password)
