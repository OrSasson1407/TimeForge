"""Firestore-backed VerificationCodeRepository (docs/05-DATABASE.md,
`emailVerifications/{email}`, doc id = the email being verified — flat
top-level collection like `users`, not school-scoped, since a code exists
before any school/role assignment is known.
"""

from google.cloud.firestore import Client

from app.domain.models import EmailVerification


def _to_document(verification: EmailVerification) -> dict[str, object]:
    return {
        "codeHash": verification.code_hash,
        "expiresAt": verification.expires_at,
        "attempts": verification.attempts,
    }


def _from_document(email: str, data: dict[str, object]) -> EmailVerification:
    return EmailVerification(
        email=email,
        code_hash=str(data["codeHash"]),
        expires_at=data["expiresAt"],  # type: ignore[arg-type]
        attempts=int(data.get("attempts", 0)),  # type: ignore[arg-type]
    )


class FirestoreVerificationCodeRepository:
    def __init__(self, client: Client) -> None:
        self._collection = client.collection("emailVerifications")

    def get(self, email: str) -> EmailVerification | None:
        snapshot = self._collection.document(email).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict()
        assert data is not None
        return _from_document(email, data)

    def save(self, verification: EmailVerification) -> None:
        self._collection.document(verification.email).set(_to_document(verification))

    def record_attempt(self, email: str) -> int:
        doc_ref = self._collection.document(email)
        snapshot = doc_ref.get()
        if not snapshot.exists:
            return 0
        data = snapshot.to_dict() or {}
        attempts = int(data.get("attempts", 0)) + 1
        doc_ref.update({"attempts": attempts})
        return attempts

    def delete(self, email: str) -> None:
        self._collection.document(email).delete()
