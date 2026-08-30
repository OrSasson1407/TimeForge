"""PublishScheduleUseCase (docs/03-ARCHITECTURE.md #26 `POST
/schedules/{id}/versions/{id}/publish`): the repository's `publish()` is
where BR-005 (no hard-constraint violations) and the archive-previous/
activate-new atomicity actually live (docs/04-DESIGN.md #21) — this use
case's job is only to trigger it and record the audit trail, never to
duplicate that check.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.application.repositories import AuditRepository, ScheduleVersionRepository
from app.core.errors import NotFoundError
from app.domain.models import (
    Actor,
    AuditEntityType,
    AuditEvent,
    AuditOperation,
    ScheduleVersion,
    User,
)


@dataclass(frozen=True, slots=True)
class PublishScheduleUseCase:
    schedule_version_repository: ScheduleVersionRepository
    audit_repository: AuditRepository

    def execute(
        self, schedule_id: str, version_id: str, *, expected_version_tag: int, actor: User
    ) -> ScheduleVersion:
        self.schedule_version_repository.publish(
            schedule_id, version_id, expected_version_tag=expected_version_tag
        )
        published = self.schedule_version_repository.get(schedule_id, version_id)
        if published is None:
            raise NotFoundError(f"ScheduleVersion {version_id} not found")

        self.audit_repository.append(
            AuditEvent(
                id=f"audit_{uuid.uuid4().hex[:16]}",
                actor=Actor(user_id=actor.id, role=actor.role),
                timestamp=datetime.now(UTC),
                operation=AuditOperation.SCHEDULE_PUBLISHED,
                entity_type=AuditEntityType.SCHEDULE_VERSION,
                entity_id=version_id,
            )
        )
        return published
