"""Firestore-backed ReschedulingEventRepository (docs/05-DATABASE.md #3:
`schedules/{scheduleId}/reschedulingEvents/{eventId}`), append-only.
Runtime-verified in Phase 10 — see generic_firestore.py's module
docstring.
"""

from google.cloud.firestore import Client, CollectionReference, Query

from app.domain.models import ReschedulingEvent
from app.domain.models.enums import ReschedulingEventType
from app.domain.models.value_objects import TimeSlot


def _event_to_document(event: ReschedulingEvent) -> dict[str, object]:
    return {
        "type": event.type.value,
        "targetEntityId": event.target_entity_id,
        "affectedSlots": [
            {"dayId": slot.day_id, "timePeriodId": slot.time_period_id}
            for slot in event.affected_slots
        ],
        "reason": event.reason,
        "reportedAt": event.reported_at,
    }


def _event_from_document(
    schedule_id: str, doc_id: str, data: dict[str, object]
) -> ReschedulingEvent:
    slots_data = data.get("affectedSlots", [])
    assert isinstance(slots_data, list)
    return ReschedulingEvent(
        id=doc_id,
        schedule_id=schedule_id,
        type=ReschedulingEventType(data["type"]),  # type: ignore[arg-type]
        target_entity_id=str(data["targetEntityId"]),
        affected_slots=tuple(
            TimeSlot(day_id=str(slot["dayId"]), time_period_id=str(slot["timePeriodId"]))
            for slot in slots_data
        ),
        reason=str(data["reason"]),
        reported_at=data["reportedAt"],  # type: ignore[arg-type]
    )


class FirestoreReschedulingEventRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    def _collection(self, schedule_id: str) -> CollectionReference:
        return (
            self._client.collection("schedules")
            .document(schedule_id)
            .collection("reschedulingEvents")
        )

    def append(self, event: ReschedulingEvent) -> None:
        self._collection(event.schedule_id).document(event.id).set(_event_to_document(event))

    def list_for_schedule(self, schedule_id: str) -> list[ReschedulingEvent]:
        query = self._collection(schedule_id).order_by("reportedAt", direction=Query.DESCENDING)
        return [
            _event_from_document(schedule_id, doc.id, doc.to_dict() or {}) for doc in query.stream()
        ]
