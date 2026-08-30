from datetime import UTC, datetime

import pytest

from app.domain.models.enums import ReschedulingEventType
from app.domain.models.rescheduling import ReschedulingEvent
from app.domain.models.value_objects import TimeSlot
from app.domain.rescheduling.affected import (
    UnsupportedReschedulingEventTypeError,
    identify_affected_assignments,
)
from app.domain.scheduling.candidate import CandidateAssignment

SLOT_A = TimeSlot(day_id="mon", time_period_id="p1")
SLOT_B = TimeSlot(day_id="mon", time_period_id="p2")


def _event(
    event_type: ReschedulingEventType, target: str, slots: tuple[TimeSlot, ...]
) -> ReschedulingEvent:
    return ReschedulingEvent(
        id="ev1",
        schedule_id="sch1",
        type=event_type,
        target_entity_id=target,
        affected_slots=slots,
        reason="test",
        reported_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_teacher_unavailable_selects_matching_teacher_and_slot() -> None:
    assignments = [
        CandidateAssignment(
            lesson_id="l1", class_id="c1", teacher_id="t1", room_id="r1", time_slot=SLOT_A
        ),
        CandidateAssignment(
            lesson_id="l2", class_id="c1", teacher_id="t1", room_id="r1", time_slot=SLOT_B
        ),
        CandidateAssignment(
            lesson_id="l3", class_id="c1", teacher_id="t2", room_id="r1", time_slot=SLOT_A
        ),
    ]
    event = _event(ReschedulingEventType.TEACHER_UNAVAILABLE, "t1", (SLOT_A,))

    affected = identify_affected_assignments(assignments, event)

    assert [a.lesson_id for a in affected] == ["l1"]


def test_room_unavailable_selects_matching_room_and_slot() -> None:
    assignments = [
        CandidateAssignment(
            lesson_id="l1", class_id="c1", teacher_id="t1", room_id="r1", time_slot=SLOT_A
        ),
        CandidateAssignment(
            lesson_id="l2", class_id="c1", teacher_id="t2", room_id="r2", time_slot=SLOT_A
        ),
    ]
    event = _event(ReschedulingEventType.ROOM_UNAVAILABLE, "r1", (SLOT_A,))

    affected = identify_affected_assignments(assignments, event)

    assert [a.lesson_id for a in affected] == ["l1"]


def test_no_matching_assignments_returns_empty() -> None:
    assignments = [
        CandidateAssignment(
            lesson_id="l1", class_id="c1", teacher_id="t1", room_id="r1", time_slot=SLOT_B
        ),
    ]
    event = _event(ReschedulingEventType.TEACHER_UNAVAILABLE, "t1", (SLOT_A,))

    assert identify_affected_assignments(assignments, event) == ()


def test_unsupported_event_type_raises() -> None:
    event = _event(ReschedulingEventType.TEACHER_REPLACED, "t1", (SLOT_A,))

    with pytest.raises(UnsupportedReschedulingEventTypeError):
        identify_affected_assignments([], event)
