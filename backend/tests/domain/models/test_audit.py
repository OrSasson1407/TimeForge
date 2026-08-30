from datetime import UTC, datetime

import pytest

from app.domain.models.audit import Actor, AuditEvent
from app.domain.models.enums import AuditEntityType, AuditOperation, UserRole


def test_audit_event_valid() -> None:
    event = AuditEvent(
        id="ae1",
        actor=Actor(user_id="user_dana", role=UserRole.ADMIN),
        timestamp=datetime(2026, 2, 3, 14, 22, tzinfo=UTC),
        operation=AuditOperation.RESCHEDULED,
        entity_type=AuditEntityType.SCHEDULE_VERSION,
        entity_id="v8",
        after={"disruptionCost": 14},
        reason="Teacher unavailable Tue P3",
    )

    assert event.operation is AuditOperation.RESCHEDULED
    assert event.before is None


def test_actor_rejects_empty_user_id() -> None:
    with pytest.raises(ValueError, match="user_id"):
        Actor(user_id="", role=UserRole.ADMIN)


def test_audit_event_rejects_empty_entity_id() -> None:
    with pytest.raises(ValueError, match="entity_id"):
        AuditEvent(
            id="ae1",
            actor=Actor(user_id="user_dana", role=UserRole.ADMIN),
            timestamp=datetime(2026, 2, 3, tzinfo=UTC),
            operation=AuditOperation.SCHEDULE_PUBLISHED,
            entity_type=AuditEntityType.SCHEDULE_VERSION,
            entity_id="",
        )
