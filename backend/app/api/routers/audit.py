"""`/audit` — admin-only, read-only (docs/05-DATABASE.md #21: append-only,
never exposed for write via the API at all)."""

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_audit_repository, require_admin
from app.api.schemas.audit import AuditEventResponse, audit_event_to_response
from app.application.repositories import AuditRepository
from app.core.errors import ValidationError
from app.domain.models import AuditEntityType, User

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditEventResponse])
def list_audit_events(
    entity_type: AuditEntityType | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    actor_user_id: str | None = Query(default=None),
    _user: User = Depends(require_admin),
    repository: AuditRepository = Depends(get_audit_repository),
) -> list[AuditEventResponse]:
    if entity_type is not None and entity_id is not None:
        events = repository.list_for_entity(entity_type, entity_id)
    elif actor_user_id is not None:
        events = repository.list_for_actor(actor_user_id)
    else:
        raise ValidationError(
            "Provide either (entity_type and entity_id) or actor_user_id to filter the audit log"
        )
    return [audit_event_to_response(event) for event in events]
