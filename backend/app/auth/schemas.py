"""Request/response schemas for registration, login and token refresh."""

from pydantic import BaseModel, Field

PHONE_PATTERN = r"^\+224\d{9}$"


class RegisterRequest(BaseModel):
    phone: str = Field(pattern=PHONE_PATTERN, description="Format international, ex: +224621234567")
    password: str = Field(min_length=8)
    email: str | None = None


class LoginRequest(BaseModel):
    phone: str = Field(pattern=PHONE_PATTERN)
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
