from datetime import UTC, datetime

import pytest

from app.domain.models.enums import ReschedulingEventType
from app.domain.models.rescheduling import ReschedulingEvent
from app.domain.models.value_objects import TimeSlot


def test_rescheduling_event_valid() -> None:
    event = ReschedulingEvent(
        id="ev1",
        schedule_id="sch1",
        type=ReschedulingEventType.TEACHER_UNAVAILABLE,
        target_entity_id="t1",
        affected_slots=(TimeSlot(day_id="day_tue", time_period_id="p3"),),
        reason="Teacher sick leave",
        reported_at=datetime(2026, 3, 10, tzinfo=UTC),
    )

    assert event.type is ReschedulingEventType.TEACHER_UNAVAILABLE


def test_rescheduling_event_rejects_empty_reason() -> None:
    with pytest.raises(ValueError, match="reason"):
        ReschedulingEvent(
            id="ev1",
            schedule_id="sch1",
            type=ReschedulingEventType.ROOM_UNAVAILABLE,
            target_entity_id="room_301",
            affected_slots=(TimeSlot(day_id="day_tue", time_period_id="p3"),),
            reason="",
            reported_at=datetime(2026, 3, 10, tzinfo=UTC),
        )


def test_rescheduling_event_rejects_no_affected_slots() -> None:
    with pytest.raises(ValueError, match="affected_slots"):
        ReschedulingEvent(
            id="ev1",
            schedule_id="sch1",
            type=ReschedulingEventType.ROOM_UNAVAILABLE,
            target_entity_id="room_301",
            affected_slots=(),
            reason="Room closed for maintenance",
            reported_at=datetime(2026, 3, 10, tzinfo=UTC),
        )
