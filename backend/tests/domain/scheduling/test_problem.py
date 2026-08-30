import pytest

from app.domain.models import LessonRequirement
from app.domain.models.lesson import Lesson
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling import (
    EMPTY_SCHEDULE_STATE,
    ScheduleState,
    SchedulingProblem,
    build_time_slots,
)
from app.domain.scheduling.candidate import CandidateAssignment

from .conftest import build_problem


def test_build_time_slots_excludes_inactive_days_and_breaks(two_days, three_periods) -> None:
    two_days[1] = two_days[1].__class__(
        id="day_tue", school_id="s1", weekday=two_days[1].weekday, is_active=False
    )

    slots = build_time_slots(two_days, three_periods)

    # day_tue is inactive; p2 is a BREAK on the remaining day -> only p1/p3 survive.
    assert slots == (
        TimeSlot(day_id="day_mon", time_period_id="p1"),
        TimeSlot(day_id="day_mon", time_period_id="p3"),
    )


def test_candidate_slots_for_excludes_periods_with_no_available_teacher(
    two_days, three_periods, two_classes, two_teachers, two_rooms, math_requirement
) -> None:
    problem = build_problem(
        days=two_days,
        periods=three_periods,
        classes=two_classes,
        teachers=two_teachers,
        rooms=two_rooms,
        requirements=[math_requirement],
    )
    lesson = problem.lessons[0]

    slots = problem.candidate_slots_for(lesson)

    assert set(slots) == {
        TimeSlot(day_id="day_mon", time_period_id="p1"),
        TimeSlot(day_id="day_mon", time_period_id="p3"),
        TimeSlot(day_id="day_tue", time_period_id="p1"),
        TimeSlot(day_id="day_tue", time_period_id="p3"),
    }


def test_candidate_slots_for_is_empty_without_a_qualified_teacher(
    two_days, three_periods, two_classes, two_rooms, math_requirement
) -> None:
    problem = build_problem(
        days=two_days,
        periods=three_periods,
        classes=two_classes,
        teachers=[],
        rooms=two_rooms,
        requirements=[math_requirement],
    )

    assert problem.candidate_slots_for(problem.lessons[0]) == ()


def test_resolve_placement_returns_a_free_teacher_and_room(
    two_days, three_periods, two_classes, two_teachers, two_rooms, math_requirement
) -> None:
    problem = build_problem(
        days=two_days,
        periods=three_periods,
        classes=two_classes,
        teachers=two_teachers,
        rooms=two_rooms,
        requirements=[math_requirement],
    )
    lesson = problem.lessons[0]
    slot = TimeSlot(day_id="day_mon", time_period_id="p1")

    candidate = problem.resolve_placement(lesson, slot, EMPTY_SCHEDULE_STATE)

    assert candidate is not None
    assert candidate.teacher_id in {"t1", "t2"}
    assert candidate.room_id in {"r1", "r2"}
    assert candidate.class_id == "c1"


def test_resolve_placement_skips_a_teacher_already_booked_at_that_slot(
    two_days, three_periods, two_classes, two_teachers, two_rooms, math_requirement
) -> None:
    problem = build_problem(
        days=two_days,
        periods=three_periods,
        classes=two_classes,
        teachers=two_teachers,
        rooms=two_rooms,
        requirements=[math_requirement],
    )
    slot = TimeSlot(day_id="day_mon", time_period_id="p1")
    busy_state = ScheduleState(
        assignments=(
            CandidateAssignment(
                lesson_id="other", class_id="c2", teacher_id="t1", room_id="r1", time_slot=slot
            ),
        )
    )

    candidate = problem.resolve_placement(problem.lessons[0], slot, busy_state)

    assert candidate is not None
    assert candidate.teacher_id == "t2"


def test_resolve_placement_returns_none_when_class_already_busy(
    two_days, three_periods, two_classes, two_teachers, two_rooms, math_requirement
) -> None:
    problem = build_problem(
        days=two_days,
        periods=three_periods,
        classes=two_classes,
        teachers=two_teachers,
        rooms=two_rooms,
        requirements=[math_requirement],
    )
    slot = TimeSlot(day_id="day_mon", time_period_id="p1")
    busy_state = ScheduleState(
        assignments=(
            CandidateAssignment(
                lesson_id="other", class_id="c1", teacher_id="t1", room_id="r1", time_slot=slot
            ),
        )
    )

    assert problem.resolve_placement(problem.lessons[0], slot, busy_state) is None


def test_scheduling_problem_rejects_lesson_with_unknown_requirement() -> None:
    orphan_lesson = Lesson(id="orphan", requirement_id="does_not_exist", sequence_index=1)

    with pytest.raises(ValueError, match="unknown requirements"):
        SchedulingProblem(
            school_id="s1",
            lessons=(orphan_lesson,),
            requirements=(),
            time_slots=(),
            teachers=(),
            classes=(),
            rooms=(),
            availability=(),
            hard_constraints=(),
        )


def test_eligible_rooms_for_filters_by_capacity_and_capability(
    two_days, three_periods, two_classes, two_teachers, two_rooms
) -> None:
    requirement = LessonRequirement(
        id="req_lab",
        school_id="s1",
        class_id="c1",
        subject_id="CHEM",
        weekly_periods=1,
        required_capability="LAB",
    )
    problem = build_problem(
        days=two_days,
        periods=three_periods,
        classes=two_classes,
        teachers=two_teachers,
        rooms=two_rooms,
        requirements=[requirement],
    )

    eligible = problem.eligible_rooms_for(requirement, two_classes[0])

    assert eligible == ()  # neither room has the LAB capability
