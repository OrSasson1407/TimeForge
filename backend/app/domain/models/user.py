"""User entity (docs/05-DATABASE.md #22).

The backend's authorization source of truth: id is the Firebase Auth UID,
resolved from the verified ID token on every request (docs/03-ARCHITECTURE.md
#23-24) — never trusted from a client-supplied role field.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.models.enums import UserRole


@dataclass(frozen=True, slots=True)
class User:
    id: str
    role: UserRole
    school_id: str
    display_name: str
    teacher_id: str | None = None
    email_verified: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("User.id must not be empty")
        if not self.school_id:
            raise ValueError("User.school_id must not be empty")
        if not self.display_name:
            raise ValueError("User.display_name must not be empty")
        if self.role is UserRole.TEACHER and not self.teacher_id:
            raise ValueError("User.teacher_id is required when role is TEACHER")
