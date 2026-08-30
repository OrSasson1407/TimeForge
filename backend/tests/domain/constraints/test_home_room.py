from app.domain.constraints.home_room import HomeRoomPreferenceConstraint
from app.domain.models.class_ import Class
from app.domain.models.lesson import Lesson, LessonRequirement
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.state import ScheduleState

from .conftest import make_candidate

SLOT = TimeSlot(day_id="day_mon", time_period_id="p1")


def _class_with_home_room() -> Class:
    return Class(
        id="c1", school_id="s1", name="7A", grade=7, student_count=25, home_room_id="room_home"
    )


def test_no_penalty_when_assigned_to_home_room() -> None:
    requirement = LessonRequirement(
        id="req1", school_id="s1", class_id="c1", subject_id="MATH", weekly_periods=1
    )
    lesson = Lesson(id="l1", requirement_id="req1", sequence_index=1)
    constraint = HomeRoomPreferenceConstraint(
        weight=1.0, classes=[_class_with_home_room()], lessons=[lesson], requirements=[requirement]
    )
    state = ScheduleState(
        assignments=(
            make_candidate(lesson_id="l1", class_id="c1", room_id="room_home", time_slot=SLOT),
        )
    )

    assert constraint.penalty(state) == 0.0


def test_penalizes_non_specialized_lesson_outside_home_room() -> None:
    requirement = LessonRequirement(
        id="req1", school_id="s1", class_id="c1", subject_id="MATH", weekly_periods=1
    )
    lesson = Lesson(id="l1", requirement_id="req1", sequence_index=1)
    constraint = HomeRoomPreferenceConstraint(
        weight=0.5, classes=[_class_with_home_room()], lessons=[lesson], requirements=[requirement]
    )
    state = ScheduleState(
        assignments=(
            make_candidate(lesson_id="l1", class_id="c1", room_id="room_other", time_slot=SLOT),
        )
    )

    assert constraint.penalty(state) == 1.0
    contribution = constraint.explain(state)[0]
    assert contribution.constraint_id == "SC-007"
    assert contribution.weighted_penalty == 0.5


def test_no_penalty_for_capability_driven_lesson_outside_home_room() -> None:
    requirement = LessonRequirement(
        id="req1",
        school_id="s1",
        class_id="c1",
        subject_id="CHEM",
        weekly_periods=1,
        required_capability="CHEMISTRY_LAB",
    )
    lesson = Lesson(id="l1", requirement_id="req1", sequence_index=1)
    constraint = HomeRoomPreferenceConstraint(
        weight=1.0, classes=[_class_with_home_room()], lessons=[lesson], requirements=[requirement]
    )
    state = ScheduleState(
        assignments=(
            make_candidate(lesson_id="l1", class_id="c1", room_id="room_lab", time_slot=SLOT),
        )
    )

    assert constraint.penalty(state) == 0.0


def test_no_penalty_when_class_has_no_home_room() -> None:
    class_without_home = Class(id="c1", school_id="s1", name="7A", grade=7, student_count=25)
    requirement = LessonRequirement(
        id="req1", school_id="s1", class_id="c1", subject_id="MATH", weekly_periods=1
    )
    lesson = Lesson(id="l1", requirement_id="req1", sequence_index=1)
    constraint = HomeRoomPreferenceConstraint(
        weight=1.0, classes=[class_without_home], lessons=[lesson], requirements=[requirement]
    )
    state = ScheduleState(
        assignments=(
            make_candidate(lesson_id="l1", class_id="c1", room_id="room_other", time_slot=SLOT),
        )
    )

    assert constraint.penalty(state) == 0.0
