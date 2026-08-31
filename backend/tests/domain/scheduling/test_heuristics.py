from app.domain.models import Lesson, LessonRequirement
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling import EMPTY_SCHEDULE_STATE, build_lesson_domains, compute_degrees
from app.domain.scheduling.heuristics import (
    forward_check,
    forward_check_detailed,
    least_constraining_value_order,
    select_next_lesson,
)

from .conftest import build_problem

SLOT_A = TimeSlot(day_id="day_mon", time_period_id="p1")
SLOT_B = TimeSlot(day_id="day_mon", time_period_id="p3")


def test_compute_degrees_counts_siblings_in_the_same_class(
    two_days, three_periods, two_classes, two_teachers, two_rooms
) -> None:
    requirements = [
        LessonRequirement(
            id="req_c1_math", school_id="s1", class_id="c1", subject_id="MATH", weekly_periods=2
        ),
        LessonRequirement(
            id="req_c2_math", school_id="s1", class_id="c2", subject_id="MATH", weekly_periods=1
        ),
    ]
    problem = build_problem(
        days=two_days,
        periods=three_periods,
        classes=two_classes,
        teachers=two_teachers,
        rooms=two_rooms,
        requirements=requirements,
    )

    degrees = compute_degrees(problem.lessons, problem)

    # c1 has 2 lessons -> each has 1 "sibling"; c2 has 1 lesson -> 0 siblings.
    assert degrees["req_c1_math_1"] == 1
    assert degrees["req_c1_math_2"] == 1
    assert degrees["req_c2_math_1"] == 0


def test_select_next_lesson_picks_the_smallest_domain() -> None:
    lesson_a = Lesson(id="a", requirement_id="req", sequence_index=1)
    lesson_b = Lesson(id="b", requirement_id="req", sequence_index=2)
    remaining = ((lesson_a, (SLOT_A, SLOT_B)), (lesson_b, (SLOT_A,)))

    index = select_next_lesson(remaining, degrees={"a": 0, "b": 0})

    assert index == 1  # lesson_b has only 1 candidate slot


def test_select_next_lesson_breaks_ties_by_higher_degree() -> None:
    lesson_a = Lesson(id="a", requirement_id="req", sequence_index=1)
    lesson_b = Lesson(id="b", requirement_id="req", sequence_index=2)
    remaining = ((lesson_a, (SLOT_A,)), (lesson_b, (SLOT_A,)))

    index = select_next_lesson(remaining, degrees={"a": 0, "b": 5})

    assert index == 1  # same domain size, lesson_b is more constrained


def test_least_constraining_value_order_prefers_the_least_contended_slot() -> None:
    other_lesson = Lesson(id="other", requirement_id="req", sequence_index=1)
    rest = ((other_lesson, (SLOT_A,)),)  # only SLOT_A is contended by another lesson

    ordered = least_constraining_value_order((SLOT_A, SLOT_B), rest)

    assert ordered == (SLOT_B, SLOT_A)


def test_least_constraining_value_order_is_a_no_op_for_singleton_domains() -> None:
    assert least_constraining_value_order((SLOT_A,), ()) == (SLOT_A,)


def test_forward_check_prunes_slots_that_are_no_longer_placeable(
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
    domains = build_lesson_domains(problem.lessons, problem)

    result = forward_check(EMPTY_SCHEDULE_STATE, domains, problem)

    assert result is not None
    assert all(len(domain) > 0 for _, domain in result)


def test_forward_check_returns_none_when_a_domain_becomes_empty(
    two_days, three_periods, two_classes, two_rooms, math_requirement
) -> None:
    problem = build_problem(
        days=two_days,
        periods=three_periods,
        classes=two_classes,
        teachers=[],  # no teacher can ever teach this lesson
        rooms=two_rooms,
        requirements=[math_requirement],
    )
    lesson = problem.lessons[0]
    domains = ((lesson, (SLOT_A,)),)

    assert forward_check(EMPTY_SCHEDULE_STATE, domains, problem) is None


def test_incremental_forward_check_matches_a_full_rescan(
    two_days, three_periods, two_classes, two_teachers, two_rooms
) -> None:
    """The correctness property behind the incremental path: because
    `resolve_placement` only ever consults state *at the slot being tested*,
    re-checking just the slot that was consumed must produce byte-identical
    domains to re-checking everything. If this ever diverges, the search is
    silently exploring a different (wrong) tree — so it is asserted for
    every slot in the problem, not just a convenient one.
    """
    requirements = [
        LessonRequirement(
            id="req_c1_math", school_id="s1", class_id="c1", subject_id="MATH", weekly_periods=2
        ),
        LessonRequirement(
            id="req_c2_math", school_id="s1", class_id="c2", subject_id="MATH", weekly_periods=2
        ),
    ]
    problem = build_problem(
        days=two_days,
        periods=three_periods,
        classes=two_classes,
        teachers=two_teachers,
        rooms=two_rooms,
        requirements=requirements,
    )
    domains = build_lesson_domains(problem.lessons, problem)
    placed, rest = domains[0], domains[1:]

    for slot in placed[1]:
        candidate = problem.resolve_placement(placed[0], slot, EMPTY_SCHEDULE_STATE)
        assert candidate is not None
        state = EMPTY_SCHEDULE_STATE.with_assignment(candidate)

        full = forward_check_detailed(state, rest, problem)
        incremental = forward_check_detailed(state, rest, problem, changed_slot=slot)

        assert incremental.pruned == full.pruned
        assert (incremental.wiped_out is None) == (full.wiped_out is None)
