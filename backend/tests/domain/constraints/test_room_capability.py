from app.domain.constraints.room_capability import RoomCapabilityConstraint
from app.domain.models.lesson import Lesson, LessonRequirement
from app.domain.models.room import Room
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.state import EMPTY_SCHEDULE_STATE

from .conftest import make_candidate

SLOT = TimeSlot(day_id="day_mon", time_period_id="p1")


def _constraint(rooms: list[Room]) -> RoomCapabilityConstraint:
    requirement = LessonRequirement(
        id="req1",
        school_id="s1",
        class_id="c1",
        subject_id="subj_chem",
        weekly_periods=2,
        required_capability="CHEMISTRY_LAB",
    )
    lesson = Lesson(id="l1", requirement_id="req1", sequence_index=1)
    return RoomCapabilityConstraint(lessons=[lesson], requirements=[requirement], rooms=rooms)


def test_room_with_required_capability_is_satisfied(lab_room: Room) -> None:
    constraint = _constraint(rooms=[lab_room])
    candidate = make_candidate(lesson_id="l1", room_id=lab_room.id, time_slot=SLOT)

    assert constraint.is_satisfied(EMPTY_SCHEDULE_STATE, candidate) is True


def test_room_missing_required_capability_is_blocked(room: Room) -> None:
    constraint = _constraint(rooms=[room])
    candidate = make_candidate(lesson_id="l1", room_id=room.id, time_slot=SLOT)

    assert constraint.is_satisfied(EMPTY_SCHEDULE_STATE, candidate) is False
    violation = constraint.explain_violation(EMPTY_SCHEDULE_STATE, candidate)
    assert violation.constraint_id == "HC-004"
    assert "CHEMISTRY_LAB" in violation.involved_entities


def test_lesson_without_required_capability_accepts_any_room(room: Room) -> None:
    requirement = LessonRequirement(
        id="req2", school_id="s1", class_id="c1", subject_id="subj_math", weekly_periods=5
    )
    lesson = Lesson(id="l2", requirement_id="req2", sequence_index=1)
    constraint = RoomCapabilityConstraint(
        lessons=[lesson], requirements=[requirement], rooms=[room]
    )
    candidate = make_candidate(lesson_id="l2", room_id=room.id, time_slot=SLOT)

    assert constraint.is_satisfied(EMPTY_SCHEDULE_STATE, candidate) is True
