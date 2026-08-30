"""Firestore-backed AvailabilityRepository (docs/05-DATABASE.md #8, #18).
Runtime-verified in Phase 10 — see generic_firestore.py's module
docstring.
"""

from google.cloud.firestore import Client, CollectionReference, FieldFilter

from app.domain.models import Availability, OwnerType


def _to_document(availability: Availability) -> dict[str, object]:
    return {
        "schoolId": availability.school_id,
        "ownerType": availability.owner_type.value,
        "ownerId": availability.owner_id,
        "dayId": availability.day_id,
        "timePeriodId": availability.time_period_id,
        "isAvailable": availability.is_available,
        "preferenceWeight": availability.preference_weight,
    }


def _from_document(doc_id: str, data: dict[str, object]) -> Availability:
    return Availability(
        id=doc_id,
        school_id=str(data["schoolId"]),
        owner_type=OwnerType(data["ownerType"]),  # type: ignore[arg-type]
        owner_id=str(data["ownerId"]),
        day_id=data.get("dayId"),  # type: ignore[arg-type]
        time_period_id=str(data["timePeriodId"]),
        is_available=bool(data["isAvailable"]),
        preference_weight=float(data.get("preferenceWeight", 0.0)),  # type: ignore[arg-type]
    )


class FirestoreAvailabilityRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    def _collection(self, school_id: str) -> CollectionReference:
        return self._client.collection("schools").document(school_id).collection("availability")

    def list_for_owner(
        self, school_id: str, owner_type: OwnerType, owner_id: str
    ) -> list[Availability]:
        # docs/05-DATABASE.md #8: composite index on (ownerType, ownerId).
        query = (
            self._collection(school_id)
            .where(filter=FieldFilter("ownerType", "==", owner_type.value))
            .where(filter=FieldFilter("ownerId", "==", owner_id))
        )
        return [_from_document(doc.id, doc.to_dict() or {}) for doc in query.stream()]

    def list_all(self, school_id: str) -> list[Availability]:
        return [
            _from_document(doc.id, doc.to_dict() or {})
            for doc in self._collection(school_id).stream()
        ]

    def save(self, school_id: str, availability: Availability) -> None:
        self._collection(school_id).document(availability.id).set(_to_document(availability))
