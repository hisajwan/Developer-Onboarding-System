from fastapi import APIRouter, Response, status

from app.api.deps import SessionDep, UserProfileServiceDep
from app.api.session_cookie import clear_session_cookie
from app.schemas.profile import (
    ChangePasswordRequest,
    DeleteAccountRequest,
    ProfileResponse,
    UpdateProfileRequest,
)

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


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    request: DeleteAccountRequest,
    response: Response,
    username: SessionDep,
    service: UserProfileServiceDep,
) -> None:
    """Deletes the account and everything it owns, after checking the password, and logs out."""
    await service.delete_account(username, request.password)
    clear_session_cookie(response)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: ChangePasswordRequest, username: SessionDep, service: UserProfileServiceDep
) -> None:
    await service.change_password(username, request.current_password, request.new_password)
