from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.domain.models import User, UserRole


class UserResponse(BaseModel):
    id: str
    role: UserRole
    school_id: str
    display_name: str
    teacher_id: str | None = None
    email_verified: bool
    is_active: bool
    created_at: datetime


def user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        role=user.role,
        school_id=user.school_id,
        display_name=user.display_name,
        teacher_id=user.teacher_id,
        email_verified=user.email_verified,
        is_active=user.is_active,
        created_at=user.created_at,
    )


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    display_name: str = Field(min_length=1, max_length=200)
    school_id: str = Field(min_length=1)
    recaptcha_token: str = Field(min_length=1)


class RegisterResponse(BaseModel):
    user_id: str
    email: str
    message: str = "Registered. Check your email for a verification code."


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=1, max_length=12)

    @field_validator("code")
    @classmethod
    def _strip_whitespace(cls, value: str) -> str:
        return value.strip()


class ResendCodeRequest(BaseModel):
    email: EmailStr


class MessageResponse(BaseModel):
    message: str


class PendingUserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    school_id: str
    created_at: datetime


class ApproveUserRequest(BaseModel):
    role: UserRole
    teacher_id: str | None = None

    @field_validator("role")
    @classmethod
    def _role_must_be_grantable(cls, value: UserRole) -> UserRole:
        if value is UserRole.PENDING:
            raise ValueError("Cannot approve a user into the PENDING role")
        return value


class AdminUserResponse(BaseModel):
    """The admin-facing "all users" list (docs/02-PRD.md #28a) — unlike
    UserResponse (which is what a user gets back about themselves), this
    includes the email address, the way PendingUserResponse already does."""

    id: str
    email: str
    role: UserRole
    school_id: str
    display_name: str
    teacher_id: str | None = None
    is_active: bool
    created_at: datetime


class CompleteOAuthProfileRequest(BaseModel):
    """Google (or any future OAuth provider) sign-in already gives Firebase
    a verified identity and a verified email — this just fills in the
    TimeForge-specific fields a fresh Firebase Auth account doesn't carry
    (docs/02-PRD.md #28a): which school, and a display name (pre-filled
    from the provider profile by the frontend, editable)."""

    display_name: str = Field(min_length=1, max_length=200)
    school_id: str = Field(min_length=1)


__all__ = [
    "AdminUserResponse",
    "ApproveUserRequest",
    "CompleteOAuthProfileRequest",
    "MessageResponse",
    "PendingUserResponse",
    "RegisterRequest",
    "RegisterResponse",
    "ResendCodeRequest",
    "UserResponse",
    "VerifyCodeRequest",
    "user_to_response",
]
