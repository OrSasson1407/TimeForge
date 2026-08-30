"""AuditEvent entity (docs/04-DESIGN.md #1-2, #22). Append-only; an
AuditEvent is never mutated or deleted once written (docs/05-DATABASE.md #21).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.models.enums import AuditEntityType, AuditOperation, UserRole


@dataclass(frozen=True, slots=True)
class Actor:
    user_id: str
    role: UserRole

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("Actor.user_id must not be empty")


@dataclass(frozen=True, slots=True)
class AuditEvent:
    id: str
    actor: Actor
    timestamp: datetime
    operation: AuditOperation
    entity_type: AuditEntityType
    entity_id: str
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("AuditEvent.id must not be empty")
        if not self.entity_id:
            raise ValueError("AuditEvent.entity_id must not be empty")
