from app.domain.constraints.room_capacity import RoomCapacityConstraint
from app.domain.models.class_ import Class
from app.domain.models.room import Room
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.state import EMPTY_SCHEDULE_STATE

from .conftest import make_candidate

SLOT = TimeSlot(day_id="day_mon", time_period_id="p1")


def test_class_within_capacity_is_satisfied(class_7a: Class, room: Room) -> None:
    constraint = RoomCapacityConstraint(classes=[class_7a], rooms=[room])
    candidate = make_candidate(class_id=class_7a.id, room_id=room.id, time_slot=SLOT)

    assert constraint.is_satisfied(EMPTY_SCHEDULE_STATE, candidate) is True


def test_class_exceeding_capacity_is_blocked(class_7a: Class, room: Room) -> None:
    small_room = Room(
        id=room.id, school_id="s1", name=room.name, capacity=10, room_type=room.room_type
    )
    constraint = RoomCapacityConstraint(classes=[class_7a], rooms=[small_room])
    candidate = make_candidate(class_id=class_7a.id, room_id=small_room.id, time_slot=SLOT)

    assert constraint.is_satisfied(EMPTY_SCHEDULE_STATE, candidate) is False
    violation = constraint.explain_violation(EMPTY_SCHEDULE_STATE, candidate)
    assert violation.constraint_id == "HC-009"


def test_class_exactly_at_capacity_is_satisfied(class_7a: Class, room: Room) -> None:
    exact_room = Room(
        id=room.id,
        school_id="s1",
        name=room.name,
        capacity=class_7a.student_count,
        room_type=room.room_type,
    )
    constraint = RoomCapacityConstraint(classes=[class_7a], rooms=[exact_room])
    candidate = make_candidate(class_id=class_7a.id, room_id=exact_room.id, time_slot=SLOT)

    assert constraint.is_satisfied(EMPTY_SCHEDULE_STATE, candidate) is True
