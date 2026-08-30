"""Firestore-backed UserRepository (docs/05-DATABASE.md #22).
Runtime-verified in Phase 10 — see generic_firestore.py's module
docstring.
"""

from datetime import UTC, datetime

from google.cloud.firestore import Client

from app.domain.models import User, UserRole


def _to_document(user: User) -> dict[str, object]:
    return {
        "role": user.role.value,
        "schoolId": user.school_id,
        "displayName": user.display_name,
        "teacherId": user.teacher_id,
        "emailVerified": user.email_verified,
        "isActive": user.is_active,
        "createdAt": user.created_at,
    }


def _from_document(doc_id: str, data: dict[str, object]) -> User:
    return User(
        id=doc_id,
        role=UserRole(data["role"]),  # type: ignore[arg-type]
        school_id=str(data["schoolId"]),
        display_name=str(data["displayName"]),
        teacher_id=data.get("teacherId"),  # type: ignore[arg-type]
        email_verified=bool(data.get("emailVerified", False)),
        is_active=bool(data.get("isActive", True)),
        created_at=data.get("createdAt") or datetime.now(UTC),  # type: ignore[arg-type]
    )


class FirestoreUserRepository:
    def __init__(self, client: Client) -> None:
        self._collection = client.collection("users")

    def get(self, user_id: str) -> User | None:
        snapshot = self._collection.document(user_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict()
        assert data is not None
        return _from_document(user_id, data)

    def save(self, user: User) -> None:
        self._collection.document(user.id).set(_to_document(user))

    def list_by_role(self, role: UserRole) -> list[User]:
        query = self._collection.where("role", "==", role.value)
        return [_from_document(doc.id, doc.to_dict() or {}) for doc in query.stream()]

    def delete(self, user_id: str) -> None:
        self._collection.document(user_id).delete()
