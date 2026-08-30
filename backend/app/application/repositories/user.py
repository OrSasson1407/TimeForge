"""UserRepository (docs/05-DATABASE.md #22): the backend's authorization
source of truth, keyed by Firebase Auth UID. `save` exists because the
backend itself provisions users (e.g. an admin inviting a teacher) —
clients never write this collection directly (Firestore rules: `write: if
false`, docs/05-DATABASE.md #10).
"""

from typing import Protocol

from app.domain.models import User, UserRole


class UserRepository(Protocol):
    def get(self, user_id: str) -> User | None: ...

    def save(self, user: User) -> None: ...

    def list_by_role(self, role: UserRole) -> list[User]:
        """Used by the admin approval queue (PENDING) — small, unbounded
        result set is an accepted scope limit (approvals are expected to
        be handled promptly, not queued up indefinitely)."""
        ...

    def delete(self, user_id: str) -> None: ...
