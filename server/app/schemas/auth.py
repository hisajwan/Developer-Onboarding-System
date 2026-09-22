from pydantic import BaseModel, Field

_USERNAME_PATTERN = r"^[A-Za-z0-9_.-]+$"
_EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=1, max_length=200)


class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254, pattern=_EMAIL_PATTERN)
    username: str = Field(min_length=3, max_length=50, pattern=_USERNAME_PATTERN)
    password: str = Field(min_length=8, max_length=200)


class SessionResponse(BaseModel):
    username: str
    last_project_id: str | None = None
