"""Generic Firestore-backed repository (docs/05-DATABASE.md #3): backs the
school-scoped catalog/config collections (Teacher, Class, Subject, Room,
SchoolDay, TimePeriod, LessonRequirement) that all share the exact
`Repository[T]` shape (docs/04-DESIGN.md #7-8, `app.application.repositories.generic`).

RUNTIME-VERIFIED in Phase 10 against a real `firebase emulators:start`
(Firestore + Auth, JDK 21) — the JDK 17 gap noted through Phases 6-9 is
resolved. `scripts/seed.py` wrote a full demo school through every
Firestore-backed repository (this one, plus School/Availability/
Schedule/ScheduleVersion/ScheduleAssignment/ReschedulingEvent/Audit/User),
and the real API (`uvicorn` against the same emulator, a real Auth
sign-in, real ID tokens) was driven through the full generate → publish →
reschedule workflow end to end, including the `@firestore.transactional`
publish path. See root `README.md`'s Project Status for a summary of what
was exercised.
"""

from collections.abc import Callable

from google.cloud.firestore import Client, CollectionReference


class FirestoreRepository[T]:
    def __init__(
        self,
        client: Client,
        *,
        collection_name: str,
        to_document: Callable[[T], dict[str, object]],
        from_document: Callable[[str, dict[str, object]], T],
    ) -> None:
        self._client = client
        self._collection_name = collection_name
        self._to_document = to_document
        self._from_document = from_document

    def _collection(self, school_id: str) -> CollectionReference:
        return (
            self._client.collection("schools").document(school_id).collection(self._collection_name)
        )

    def get(self, school_id: str, entity_id: str) -> T | None:
        snapshot = self._collection(school_id).document(entity_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict()
        assert data is not None  # exists=True guarantees a body
        return self._from_document(entity_id, data)

    def list(self, school_id: str) -> list[T]:
        return [
            self._from_document(doc.id, doc.to_dict() or {})
            for doc in self._collection(school_id).stream()
        ]

    def save(self, school_id: str, entity: T) -> None:
        entity_id: str = entity.id  # type: ignore[attr-defined]
        self._collection(school_id).document(entity_id).set(self._to_document(entity))
