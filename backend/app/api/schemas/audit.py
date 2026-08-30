from datetime import datetime

from pydantic import BaseModel

from app.domain.models import AuditEntityType, AuditEvent, AuditOperation, UserRole


class ActorResponse(BaseModel):
    user_id: str
    role: UserRole


class AuditEventResponse(BaseModel):
    id: str
    actor: ActorResponse
    timestamp: datetime
    operation: AuditOperation
    entity_type: AuditEntityType
    entity_id: str
    before: dict[str, object] | None = None
    after: dict[str, object] | None = None
    reason: str | None = None


def audit_event_to_response(event: AuditEvent) -> AuditEventResponse:
    return AuditEventResponse(
        id=event.id,
        actor=ActorResponse(user_id=event.actor.user_id, role=event.actor.role),
        timestamp=event.timestamp,
        operation=event.operation,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        before=event.before,
        after=event.after,
        reason=event.reason,
    )
