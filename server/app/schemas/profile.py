from pydantic import BaseModel, Field

from app.domain.models import User


class ProfileResponse(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: str

    @classmethod
    def from_domain(cls, user: User) -> "ProfileResponse":
        return cls(
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
        )


class UpdateProfileRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)
