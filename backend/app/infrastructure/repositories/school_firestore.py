"""Firestore-backed SchoolRepository. Runtime-verified in Phase 10 — see
generic_firestore.py's module docstring."""

from google.cloud.firestore import Client

from app.domain.models import School


def _school_to_document(school: School) -> dict[str, object]:
    return {"name": school.name, "timezone": school.timezone}


def _school_from_document(doc_id: str, data: dict[str, object]) -> School:
    return School(id=doc_id, name=str(data["name"]), timezone=str(data["timezone"]))


class FirestoreSchoolRepository:
    def __init__(self, client: Client) -> None:
        self._collection = client.collection("schools")

    def get(self, school_id: str) -> School | None:
        snapshot = self._collection.document(school_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict()
        assert data is not None
        return _school_from_document(school_id, data)

    def list(self) -> list[School]:
        return [
            _school_from_document(doc.id, doc.to_dict() or {}) for doc in self._collection.stream()
        ]

    def save(self, school: School) -> None:
        self._collection.document(school.id).set(_school_to_document(school))
