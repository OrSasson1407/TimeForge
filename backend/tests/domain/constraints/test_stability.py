import pytest

from app.domain.constraints.stability import (
    DisruptionMinimizationConstraint,
    PreservationConstraint,
)
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.state import ScheduleState

from .conftest import make_candidate

SLOT_A = TimeSlot("day_mon", "p1")
SLOT_B = TimeSlot("day_tue", "p1")

_ConstraintCls = type[DisruptionMinimizationConstraint] | type[PreservationConstraint]


@pytest.mark.parametrize(
    "constraint_cls,expected_id",
    [(DisruptionMinimizationConstraint, "SC-009"), (PreservationConstraint, "SC-010")],
)
def test_no_penalty_when_state_matches_baseline(
    constraint_cls: _ConstraintCls, expected_id: str
) -> None:
    baseline = (make_candidate(lesson_id="l1", teacher_id="t1", time_slot=SLOT_A),)
    constraint = constraint_cls(weight=1.0, baseline=baseline)
    state = ScheduleState(assignments=baseline)

    assert constraint.penalty(state) == 0.0
    assert constraint.explain(state) == []
    assert constraint.id == expected_id


@pytest.mark.parametrize(
    "constraint_cls", [DisruptionMinimizationConstraint, PreservationConstraint]
)
def test_penalizes_lessons_that_moved(constraint_cls: _ConstraintCls) -> None:
    baseline = (
        make_candidate(lesson_id="l1", teacher_id="t1", time_slot=SLOT_A),
        make_candidate(lesson_id="l2", teacher_id="t2", time_slot=SLOT_A),
    )
    constraint = constraint_cls(weight=3.0, baseline=baseline)
    state = ScheduleState(
        assignments=(
            make_candidate(lesson_id="l1", teacher_id="t1", time_slot=SLOT_B),  # moved
            make_candidate(lesson_id="l2", teacher_id="t2", time_slot=SLOT_A),  # unchanged
        )
    )

    assert constraint.penalty(state) == 1.0
    contribution = constraint.explain(state)[0]
    assert contribution.weighted_penalty == 3.0


@pytest.mark.parametrize(
    "constraint_cls", [DisruptionMinimizationConstraint, PreservationConstraint]
)
def test_lessons_absent_from_baseline_are_ignored(constraint_cls: _ConstraintCls) -> None:
    baseline = (make_candidate(lesson_id="l1", teacher_id="t1", time_slot=SLOT_A),)
    constraint = constraint_cls(weight=1.0, baseline=baseline)
    state = ScheduleState(
        assignments=(make_candidate(lesson_id="new_lesson", teacher_id="t1", time_slot=SLOT_B),)
    )

    assert constraint.penalty(state) == 0.0
