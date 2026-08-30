from datetime import UTC, datetime

from app.domain.models import Actor, AuditEntityType, AuditEvent, AuditOperation, UserRole
from tests.api.conftest import ApiFixtures


def test_list_requires_entity_filter_or_actor_filter(api: ApiFixtures) -> None:
    api.admin()

    response = api.client.get("/audit")

    assert response.status_code == 400


def test_list_for_entity_returns_newest_first(api: ApiFixtures) -> None:
    admin = api.admin()
    api.audit.append(
        AuditEvent(
            id="ae1",
            actor=Actor(user_id=admin.id, role=UserRole.ADMIN),
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            operation=AuditOperation.SCHEDULE_GENERATED,
            entity_type=AuditEntityType.SCHEDULE_VERSION,
            entity_id="v1",
        )
    )
    api.audit.append(
        AuditEvent(
            id="ae2",
            actor=Actor(user_id=admin.id, role=UserRole.ADMIN),
            timestamp=datetime(2026, 1, 2, tzinfo=UTC),
            operation=AuditOperation.SCHEDULE_PUBLISHED,
            entity_type=AuditEntityType.SCHEDULE_VERSION,
            entity_id="v1",
        )
    )

    response = api.client.get(
        "/audit", params={"entity_type": "SCHEDULE_VERSION", "entity_id": "v1"}
    )

    assert response.status_code == 200
    assert [e["operation"] for e in response.json()] == ["SCHEDULE_PUBLISHED", "SCHEDULE_GENERATED"]


def test_non_admin_cannot_read_the_audit_log(api: ApiFixtures) -> None:
    api.teacher()

    response = api.client.get(
        "/audit", params={"entity_type": "SCHEDULE_VERSION", "entity_id": "v1"}
    )

    assert response.status_code == 403
