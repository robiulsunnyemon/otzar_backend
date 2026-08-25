from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserRead


class EmailSubmitRequest(BaseModel):
    email: EmailStr = Field(..., description="Operator email address")


class EmailSubmitResponse(BaseModel):
    email: str
    is_new_user: bool
    is_verified: bool
    message: str
    expires_in_minutes: Optional[int] = 10


class PinVerifyRequest(BaseModel):
    email: EmailStr = Field(..., description="Operator email address")
    pin: str = Field(..., min_length=4, max_length=4, description="4-digit security PIN")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid JWT refresh token")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead
