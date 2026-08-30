from datetime import UTC, datetime

from app.domain.models import Actor, AuditEntityType, AuditEvent, AuditOperation, UserRole
from tests.support.fakes import FakeAuditRepository


def _event(**overrides: object) -> AuditEvent:
    defaults: dict[str, object] = {
        "id": "ae1",
        "actor": Actor(user_id="user_dana", role=UserRole.ADMIN),
        "timestamp": datetime(2026, 2, 3, tzinfo=UTC),
        "operation": AuditOperation.SCHEDULE_PUBLISHED,
        "entity_type": AuditEntityType.SCHEDULE_VERSION,
        "entity_id": "v1",
    }
    defaults.update(overrides)
    return AuditEvent(**defaults)  # type: ignore[arg-type]


def test_list_for_entity_filters_by_type_and_id() -> None:
    repo = FakeAuditRepository()
    repo.append(_event(id="ae1", entity_type=AuditEntityType.SCHEDULE_VERSION, entity_id="v1"))
    repo.append(_event(id="ae2", entity_type=AuditEntityType.SCHEDULE_VERSION, entity_id="v2"))
    repo.append(_event(id="ae3", entity_type=AuditEntityType.TEACHER, entity_id="v1"))

    results = repo.list_for_entity(AuditEntityType.SCHEDULE_VERSION, "v1")

    assert [e.id for e in results] == ["ae1"]


def test_list_for_entity_orders_newest_first() -> None:
    repo = FakeAuditRepository()
    repo.append(_event(id="early", timestamp=datetime(2026, 1, 1, tzinfo=UTC)))
    repo.append(_event(id="late", timestamp=datetime(2026, 3, 1, tzinfo=UTC)))

    results = repo.list_for_entity(AuditEntityType.SCHEDULE_VERSION, "v1")

    assert [e.id for e in results] == ["late", "early"]


def test_list_for_actor_filters_by_user_id() -> None:
    repo = FakeAuditRepository()
    repo.append(_event(id="ae1", actor=Actor(user_id="user_dana", role=UserRole.ADMIN)))
    repo.append(_event(id="ae2", actor=Actor(user_id="user_yossi", role=UserRole.TEACHER)))

    results = repo.list_for_actor("user_dana")

    assert [e.id for e in results] == ["ae1"]
