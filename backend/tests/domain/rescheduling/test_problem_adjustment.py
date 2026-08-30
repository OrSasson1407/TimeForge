from datetime import UTC, datetime

from app.domain.models.availability import Availability
from app.domain.models.enums import OwnerType, ReschedulingEventType, RoomStatus
from app.domain.models.rescheduling import ReschedulingEvent
from app.domain.models.room import Room
from app.domain.models.value_objects import TimeSlot
from app.domain.rescheduling.problem_adjustment import (
    augment_availability_for_event,
    augment_rooms_for_event,
)

SLOT_A = TimeSlot(day_id="mon", time_period_id="p1")


def _event(event_type: ReschedulingEventType, target: str) -> ReschedulingEvent:
    return ReschedulingEvent(
        id="ev1",
        schedule_id="sch1",
        type=event_type,
        target_entity_id=target,
        affected_slots=(SLOT_A,),
        reason="test",
        reported_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_teacher_unavailable_adds_a_synthetic_unavailable_record() -> None:
    event = _event(ReschedulingEventType.TEACHER_UNAVAILABLE, "t1")

    augmented = augment_availability_for_event([], event, school_id="s1")

    assert len(augmented) == 1
    record = augmented[0]
    assert record.owner_type is OwnerType.TEACHER
    assert record.owner_id == "t1"
    assert record.day_id == "mon"
    assert record.time_period_id == "p1"
    assert record.is_available is False


def test_room_unavailable_is_a_no_op_for_availability() -> None:
    event = _event(ReschedulingEventType.ROOM_UNAVAILABLE, "r1")
    existing = [
        Availability(
            id="a1",
            school_id="s1",
            owner_type=OwnerType.TEACHER,
            owner_id="t1",
            time_period_id="p1",
            is_available=True,
        )
    ]

    assert augment_availability_for_event(existing, event, school_id="s1") == tuple(existing)


def test_room_unavailable_closes_the_target_room() -> None:
    event = _event(ReschedulingEventType.ROOM_UNAVAILABLE, "r1")
    rooms = [
        Room(id="r1", school_id="s1", name="Room 1", capacity=30, room_type="STANDARD"),
        Room(id="r2", school_id="s1", name="Room 2", capacity=30, room_type="STANDARD"),
    ]

    augmented = augment_rooms_for_event(rooms, event)

    by_id = {room.id: room for room in augmented}
    assert by_id["r1"].status is RoomStatus.CLOSED
    assert by_id["r2"].status is RoomStatus.ACTIVE


def test_teacher_unavailable_is_a_no_op_for_rooms() -> None:
    event = _event(ReschedulingEventType.TEACHER_UNAVAILABLE, "t1")
    rooms = [Room(id="r1", school_id="s1", name="Room 1", capacity=30, room_type="STANDARD")]

    assert augment_rooms_for_event(rooms, event) == tuple(rooms)
