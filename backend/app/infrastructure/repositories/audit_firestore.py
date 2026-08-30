"""Firestore-backed AuditRepository (docs/05-DATABASE.md #8, #21):
top-level `auditEvents` collection, append-only. Runtime-verified in Phase
10 — see generic_firestore.py's module docstring.
"""

from google.cloud.firestore import Client, FieldFilter, Query

from app.domain.models import Actor, AuditEntityType, AuditEvent, AuditOperation, UserRole


def _to_document(event: AuditEvent) -> dict[str, object]:
    return {
        "actor": {"userId": event.actor.user_id, "role": event.actor.role.value},
        "timestamp": event.timestamp,
        "operation": event.operation.value,
        "entityType": event.entity_type.value,
        "entityId": event.entity_id,
        "before": event.before,
        "after": event.after,
        "reason": event.reason,
    }


def _from_document(doc_id: str, data: dict[str, object]) -> AuditEvent:
    actor_data = data["actor"]
    assert isinstance(actor_data, dict)
    return AuditEvent(
        id=doc_id,
        actor=Actor(user_id=str(actor_data["userId"]), role=UserRole(actor_data["role"])),
        timestamp=data["timestamp"],  # type: ignore[arg-type]
        operation=AuditOperation(data["operation"]),  # type: ignore[arg-type]
        entity_type=AuditEntityType(data["entityType"]),  # type: ignore[arg-type]
        entity_id=str(data["entityId"]),
        before=data.get("before"),  # type: ignore[arg-type]
        after=data.get("after"),  # type: ignore[arg-type]
        reason=data.get("reason"),  # type: ignore[arg-type]
    )


class FirestoreAuditRepository:
    def __init__(self, client: Client) -> None:
        self._collection = client.collection("auditEvents")

    def append(self, event: AuditEvent) -> None:
        self._collection.document(event.id).set(_to_document(event))

    def list_for_entity(self, entity_type: AuditEntityType, entity_id: str) -> list[AuditEvent]:
        # docs/05-DATABASE.md #8: composite index on (entityType, entityId, timestamp desc).
        query = (
            self._collection.where(filter=FieldFilter("entityType", "==", entity_type.value))
            .where(filter=FieldFilter("entityId", "==", entity_id))
            .order_by("timestamp", direction=Query.DESCENDING)
        )
        return [_from_document(doc.id, doc.to_dict() or {}) for doc in query.stream()]

    def list_for_actor(self, user_id: str) -> list[AuditEvent]:
        query = self._collection.where(filter=FieldFilter("actor.userId", "==", user_id)).order_by(
            "timestamp", direction=Query.DESCENDING
        )
        return [_from_document(doc.id, doc.to_dict() or {}) for doc in query.stream()]
