"""AuditRepository (docs/04-DESIGN.md #22; docs/05-DATABASE.md #21):
append-only — there is deliberately no update/delete method. Every
application-layer use case that mutates state appends exactly one
AuditEvent in the same transaction/batch as the mutation
(docs/01-CLAUDE.md #14, #22).
"""

from typing import Protocol

from app.domain.models import AuditEntityType, AuditEvent


class AuditRepository(Protocol):
    def append(self, event: AuditEvent) -> None: ...

    def list_for_entity(self, entity_type: AuditEntityType, entity_id: str) -> list[AuditEvent]:
        """Newest first (docs/05-DATABASE.md #8's `entityType, entityId,
        timestamp desc` composite index)."""
        ...

    def list_for_actor(self, user_id: str) -> list[AuditEvent]: ...
