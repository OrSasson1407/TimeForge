import pytest

from app.domain.constraints.weekly_requirement import WeeklyRequirementConstraint
from app.domain.models.lesson import LessonRequirement
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.state import EMPTY_SCHEDULE_STATE, ScheduleState

from .conftest import make_candidate

SLOT_A = TimeSlot(day_id="day_mon", time_period_id="p1")
SLOT_B = TimeSlot(day_id="day_tue", time_period_id="p1")
SLOT_C = TimeSlot(day_id="day_wed", time_period_id="p1")


def _requirement(weekly_periods: int = 3) -> LessonRequirement:
    return LessonRequirement(
        id="req1",
        school_id="s1",
        class_id="c1",
        subject_id="subj_math",
        weekly_periods=weekly_periods,
    )


def test_is_satisfied_is_always_true_regardless_of_candidate() -> None:
    """HC-008 is monotonic: a single valid placement can never violate it."""
    requirement = _requirement()
    constraint = WeeklyRequirementConstraint(
        lessons=requirement.expand(), requirements=[requirement]
    )
    candidate = make_candidate(lesson_id="req1_1", time_slot=SLOT_A)

    assert constraint.is_satisfied(EMPTY_SCHEDULE_STATE, candidate) is True


def test_explain_violation_raises_since_is_satisfied_never_fails() -> None:
    requirement = _requirement()
    constraint = WeeklyRequirementConstraint(
        lessons=requirement.expand(), requirements=[requirement]
    )

    with pytest.raises(NotImplementedError):
        constraint.explain_violation(
            EMPTY_SCHEDULE_STATE, make_candidate(lesson_id="req1_1", time_slot=SLOT_A)
        )


def test_violations_in_flags_incomplete_requirement() -> None:
    requirement = _requirement(weekly_periods=3)
    lessons = requirement.expand()
    constraint = WeeklyRequirementConstraint(lessons=lessons, requirements=[requirement])
    # Only 1 of the 3 required lessons is placed.
    state = ScheduleState(assignments=(make_candidate(lesson_id=lessons[0].id, time_slot=SLOT_A),))

    violations = constraint.violations_in(state)

    assert len(violations) == 1
    assert violations[0].constraint_id == "HC-008"
    assert "req1" in violations[0].involved_entities


def test_violations_in_is_empty_when_fully_satisfied() -> None:
    requirement = _requirement(weekly_periods=3)
    lessons = requirement.expand()
    constraint = WeeklyRequirementConstraint(lessons=lessons, requirements=[requirement])
    state = ScheduleState(
        assignments=(
            make_candidate(lesson_id=lessons[0].id, time_slot=SLOT_A),
            make_candidate(lesson_id=lessons[1].id, time_slot=SLOT_B),
            make_candidate(lesson_id=lessons[2].id, time_slot=SLOT_C),
        )
    )

    assert constraint.violations_in(state) == []
