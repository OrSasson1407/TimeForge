"""Conflict-set analysis for conflict-directed backjumping.

The property that actually matters for correctness is stated in
`conflicts.py`'s module docstring: a conflict set may over-approximate
(the search just jumps less far) but must never under-approximate (the
search could jump past the decision that needed revisiting and lose a
solution). These tests pin the attribution down in each of the ways a
placement can be blocked.
"""

from app.domain.models import LessonRequirement
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.candidate import CandidateAssignment
from app.domain.scheduling.conflicts import (
    blocking_lesson_ids,
    domain_wipeout_culprits,
    every_assigned_lesson_id,
)
from app.domain.scheduling.state import EMPTY_SCHEDULE_STATE, ScheduleState
from tests.domain.scheduling.conftest import build_problem

SLOT_MON_P1 = TimeSlot(day_id="day_mon", time_period_id="p1")
SLOT_MON_P3 = TimeSlot(day_id="day_mon", time_period_id="p3")


def _two_class_math_problem(two_days, three_periods, two_classes, two_teachers, two_rooms):
    """Two classes each needing one MATH lesson, drawing on the same pool of
    two teachers and two rooms — enough shared resource for placements to
    block one another without being trivially infeasible."""
    requirements = [
        LessonRequirement(
            id="req_c1", school_id="s1", class_id="c1", subject_id="MATH", weekly_periods=1
        ),
        LessonRequirement(
            id="req_c2", school_id="s1", class_id="c2", subject_id="MATH", weekly_periods=1
        ),
    ]
    return build_problem(
        days=two_days,
        periods=three_periods,
        classes=two_classes,
        teachers=two_teachers,
        rooms=two_rooms,
        requirements=requirements,
    )


def test_nothing_blocks_a_placement_into_an_empty_schedule(
    two_days, three_periods, two_classes, two_teachers, two_rooms
):
    problem = _two_class_math_problem(two_days, three_periods, two_classes, two_teachers, two_rooms)
    lesson = problem.lessons[0]

    assert blocking_lesson_ids(lesson, SLOT_MON_P1, EMPTY_SCHEDULE_STATE, problem) == frozenset()


def test_a_busy_class_is_a_complete_explanation_on_its_own(
    two_days, three_periods, two_classes, two_teachers, two_rooms
):
    """When the lesson's own class is already occupied in that slot, no
    other resource matters — that single lesson fully explains the block."""
    problem = _two_class_math_problem(two_days, three_periods, two_classes, two_teachers, two_rooms)
    c1_lesson = next(lesson for lesson in problem.lessons if lesson.requirement_id == "req_c1")
    occupying = CandidateAssignment(
        lesson_id="some_other_c1_lesson",
        class_id="c1",
        teacher_id="t1",
        room_id="r1",
        time_slot=SLOT_MON_P1,
    )
    state = ScheduleState(assignments=(occupying,))

    assert blocking_lesson_ids(c1_lesson, SLOT_MON_P1, state, problem) == frozenset(
        {"some_other_c1_lesson"}
    )


def test_exhausted_teachers_and_rooms_are_all_named(
    two_days, three_periods, two_classes, two_teachers, two_rooms
):
    """With both teachers and both rooms consumed by other classes, the
    lesson cannot be placed — and every occupying lesson is a culprit,
    because freeing any of them could open the slot back up."""
    problem = _two_class_math_problem(two_days, three_periods, two_classes, two_teachers, two_rooms)
    c2_lesson = next(lesson for lesson in problem.lessons if lesson.requirement_id == "req_c2")
    # c1 occupies t1+r1; a third (hypothetical) class occupies t2+r2, so
    # nothing is left for c2 in this slot.
    state = ScheduleState(
        assignments=(
            CandidateAssignment(
                lesson_id="blocker_a",
                class_id="c1",
                teacher_id="t1",
                room_id="r1",
                time_slot=SLOT_MON_P1,
            ),
            CandidateAssignment(
                lesson_id="blocker_b",
                class_id="c3",
                teacher_id="t2",
                room_id="r2",
                time_slot=SLOT_MON_P1,
            ),
        )
    )

    culprits = blocking_lesson_ids(c2_lesson, SLOT_MON_P1, state, problem)

    assert problem.resolve_placement(c2_lesson, SLOT_MON_P1, state) is None
    assert culprits == frozenset({"blocker_a", "blocker_b"})


def test_a_placement_in_a_different_slot_never_blocks(
    two_days, three_periods, two_classes, two_teachers, two_rooms
):
    """The same property that makes incremental forward checking exact:
    assignments only ever conflict within their own time slot."""
    problem = _two_class_math_problem(two_days, three_periods, two_classes, two_teachers, two_rooms)
    c2_lesson = next(lesson for lesson in problem.lessons if lesson.requirement_id == "req_c2")
    state = ScheduleState(
        assignments=(
            CandidateAssignment(
                lesson_id="elsewhere",
                class_id="c1",
                teacher_id="t1",
                room_id="r1",
                time_slot=SLOT_MON_P3,
            ),
        )
    )

    assert blocking_lesson_ids(c2_lesson, SLOT_MON_P1, state, problem) == frozenset()


def test_wipeout_culprits_union_every_slot_that_was_lost(
    two_days, three_periods, two_classes, two_teachers, two_rooms
):
    problem = _two_class_math_problem(two_days, three_periods, two_classes, two_teachers, two_rooms)
    c2_lesson = next(lesson for lesson in problem.lessons if lesson.requirement_id == "req_c2")
    state = ScheduleState(
        assignments=(
            CandidateAssignment(
                lesson_id="blocks_p1",
                class_id="c2",
                teacher_id="t1",
                room_id="r1",
                time_slot=SLOT_MON_P1,
            ),
            CandidateAssignment(
                lesson_id="blocks_p3",
                class_id="c2",
                teacher_id="t2",
                room_id="r2",
                time_slot=SLOT_MON_P3,
            ),
        )
    )

    culprits = domain_wipeout_culprits(c2_lesson, (SLOT_MON_P1, SLOT_MON_P3), state, problem)

    assert culprits == frozenset({"blocks_p1", "blocks_p3"})


def test_every_assigned_lesson_id_is_the_safe_fallback():
    state = ScheduleState(
        assignments=(
            CandidateAssignment(
                lesson_id="a", class_id="c1", teacher_id="t1", room_id="r1", time_slot=SLOT_MON_P1
            ),
            CandidateAssignment(
                lesson_id="b", class_id="c2", teacher_id="t2", room_id="r2", time_slot=SLOT_MON_P3
            ),
        )
    )

    assert every_assigned_lesson_id(state) == frozenset({"a", "b"})
    assert every_assigned_lesson_id(EMPTY_SCHEDULE_STATE) == frozenset()
