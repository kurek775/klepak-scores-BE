import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


def _validate_password_strength(v: str) -> str:
    if len(v) < 8:
        raise ValueError('Password must be at least 8 characters')
    if not re.search(r'[A-Z]', v):
        raise ValueError('Password must contain at least one uppercase letter')
    if not re.search(r'\d', v):
        raise ValueError('Password must contain at least one digit')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
        raise ValueError('Password must contain at least one special character')
    return v


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class AcceptInvitationRequest(BaseModel):
    token: str = Field(min_length=1, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class CreateInvitationRequest(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.EVALUATOR


class InvitationRead(BaseModel):
    id: int
    email: str
    role: str
    used: bool
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
